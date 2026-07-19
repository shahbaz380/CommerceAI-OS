"""eBay MarketplaceAdapter — full OAuth connect/disconnect/refresh/reconnect."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.marketplaces.enums import ConnectionStatus, MarketplaceChannel, MarketplaceEnvironment
from app.domain.marketplaces.exceptions import (
    MarketplaceAlreadyConnected,
    MarketplaceRefreshInProgress,
    OAuthReplayAttack,
    OAuthStateExpired,
    OAuthStateInvalid,
    TokenExchangeFailed,
    TokenRefreshFailed,
)
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.marketplace.base import (
    ConnectResult,
    MarketplaceAdapter,
    MarketplaceContext,
    OAuthCallbackResult,
)
from app.infrastructure.marketplace.ebay.client.gateway import EbayApiGateway
from app.infrastructure.marketplace.ebay.oauth.client import DEFAULT_EBAY_SCOPES, EbayOAuthClient, EbayOAuthConfig
from app.infrastructure.marketplace.ebay.oauth.revocation import revoke_ebay_token
from app.infrastructure.marketplace.ebay.oauth.state_store import OAuthStateStore, TokenRefreshLock
from app.infrastructure.marketplace.http.client import AsyncHttpClient
from app.infrastructure.persistence.models.marketplace import (
    MarketplaceApiLogModel,
    MarketplaceConnectionModel,
    MarketplaceOAuthTokenModel,
    MarketplaceTokenRefreshHistoryModel,
)
from app.infrastructure.persistence.repositories.marketplace import (
    MarketplaceConnectionRepository,
    MarketplaceCredentialRepository,
    MarketplaceLogRepository,
    MarketplaceTokenRepository,
)
from app.infrastructure.persistence.repositories.tenancy import TenantAuditRepository
from app.shared.exceptions import MarketplaceError, NotFoundError, ValidationAppError

logger = get_logger("app.marketplace")


class EbayMarketplaceAdapter(MarketplaceAdapter):
    channel = MarketplaceChannel.EBAY.value

    def __init__(self, session: AsyncSession, http: AsyncHttpClient | None = None) -> None:
        self.session = session
        self.http = http or AsyncHttpClient()
        self.connections = MarketplaceConnectionRepository(session)
        self.tokens = MarketplaceTokenRepository(session)
        self.credentials = MarketplaceCredentialRepository(session)
        self.logs = MarketplaceLogRepository(session)
        self.state_store = OAuthStateStore(session)
        self.refresh_lock = TokenRefreshLock()
        self.audit = TenantAuditRepository(session)

    async def health(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "status": "ready",
            "capabilities": [
                "oauth.connect",
                "oauth.callback",
                "oauth.refresh",
                "oauth.disconnect",
                "oauth.reconnect",
                "oauth.revoke",
                "connection.validate",
                "connection.default",
            ],
            "business_apis": False,
        }

    async def _oauth_client(self, workspace_id: UUID, environment: str) -> EbayOAuthClient:
        cred = await self.credentials.get_active(workspace_id, self.channel, environment)
        if cred is None:
            raise ValidationAppError(
                "eBay developer credentials not configured for this workspace/environment",
                code="EBAY_CREDENTIALS_MISSING",
                details=[
                    {"field": "channel", "issue": "ebay"},
                    {"field": "environment", "issue": environment},
                ],
            )
        return EbayOAuthClient(
            EbayOAuthConfig(
                client_id=cred.client_id,
                client_secret=cred.client_secret_encrypted,
                redirect_uri=cred.redirect_uri,
                environment=environment,
                scopes=cred.scopes or DEFAULT_EBAY_SCOPES,
                ru_name=cred.ru_name,
            ),
            http=self.http,
        )

    async def begin_connect(self, ctx: MarketplaceContext, **kwargs: Any) -> ConnectResult:
        if ctx.user_id is None:
            raise ValidationAppError(
                "user_id required to connect marketplace",
                details=[{"field": "user_id", "issue": "required"}],
            )
        environment = kwargs.get("environment") or ctx.environment or MarketplaceEnvironment.SANDBOX
        display_name = kwargs.get("display_name")
        alias = kwargs.get("alias")
        reconnect_id = kwargs.get("connection_id")
        oauth = await self._oauth_client(ctx.workspace_id, environment)

        connection: MarketplaceConnectionModel | None = None
        if reconnect_id:
            connection = await self.connections.get_for_workspace(ctx.workspace_id, reconnect_id)
            if connection is None or connection.channel != self.channel:
                raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
            connection.status = ConnectionStatus.PENDING
            connection.disconnected_at = None
            connection.suspended_at = None
            if display_name:
                connection.display_name = display_name
            if alias is not None:
                connection.alias = alias
        else:
            connection = MarketplaceConnectionModel(
                workspace_id=ctx.workspace_id,
                channel=self.channel,
                environment=environment,
                status=ConnectionStatus.PENDING,
                display_name=display_name or "eBay account",
                alias=alias,
                connected_by_user_id=ctx.user_id,
            )
            await self.connections.add(connection)

        state_payload = await self.state_store.create(
            workspace_id=ctx.workspace_id,
            channel=self.channel,
            environment=environment,
            user_id=ctx.user_id,
            redirect_uri=oauth.config.redirect_uri,
            connection_id=connection.id,
        )
        url = oauth.build_authorization_url(state=state_payload.state)
        await self.audit.add(
            event_type="marketplace.oauth.started",
            message="eBay OAuth authorization started",
            actor_user_id=ctx.user_id,
            workspace_id=ctx.workspace_id,
            metadata={
                "connection_id": str(connection.id),
                "environment": environment,
                "channel": self.channel,
            },
        )
        await self.session.flush()
        logger.info(
            "ebay_connect_started",
            workspace_id=str(ctx.workspace_id),
            connection_id=str(connection.id),
            environment=environment,
        )
        return ConnectResult(
            connection_id=connection.id,
            status=ConnectionStatus.PENDING,
            authorization_url=url,
            state=state_payload.state,
        )

    async def complete_connect(
        self,
        ctx: MarketplaceContext,
        *,
        code: str,
        state: str,
        **kwargs: Any,
    ) -> OAuthCallbackResult:
        if not code:
            raise ValidationAppError("Authorization code is required", details=[{"field": "code"}])

        try:
            st = await self.state_store.consume(
                state,
                workspace_id=ctx.workspace_id,
                channel=self.channel,
                user_id=ctx.user_id,
            )
        except (OAuthStateInvalid, OAuthStateExpired, OAuthReplayAttack):
            await self.audit.add(
                event_type="marketplace.oauth.state_failed",
                message="OAuth state validation failed",
                actor_user_id=ctx.user_id,
                workspace_id=ctx.workspace_id,
                metadata={"channel": self.channel},
            )
            await self.session.flush()
            raise

        connection_id = UUID(st.connection_id) if st.connection_id else kwargs.get("connection_id")
        connection = None
        if connection_id:
            connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            pending = [
                c
                for c in await self.connections.list_for_workspace(ctx.workspace_id, channel=self.channel)
                if c.status == ConnectionStatus.PENDING and c.environment == st.environment
            ]
            connection = pending[0] if pending else None
        if connection is None:
            raise NotFoundError("Pending eBay connection not found", code="CONNECTION_NOT_FOUND")

        oauth = await self._oauth_client(ctx.workspace_id, st.environment)
        try:
            token_resp = await oauth.exchange_code(code=code)
        except MarketplaceError as exc:
            connection.status = ConnectionStatus.ERROR
            connection.last_error_at = datetime.now(UTC)
            connection.last_error_code = "TOKEN_EXCHANGE_FAILED"
            connection.last_error_message = str(exc)[:500]
            await self.audit.add(
                event_type="marketplace.oauth.exchange_failed",
                message="eBay token exchange failed",
                actor_user_id=ctx.user_id,
                workspace_id=ctx.workspace_id,
                metadata={"connection_id": str(connection.id), "error": str(exc)[:300]},
            )
            await self.session.flush()
            raise TokenExchangeFailed(str(exc), cause=exc) from exc

        await self.tokens.mark_all_not_current(connection.id)
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=int(token_resp.expires_in))
            if token_resp.expires_in
            else None
        )
        refresh_expires_at = (
            datetime.now(UTC) + timedelta(seconds=int(token_resp.refresh_token_expires_in))
            if token_resp.refresh_token_expires_in
            else None
        )
        await self.tokens.add(
            MarketplaceOAuthTokenModel(
                connection_id=connection.id,
                access_token_encrypted=token_resp.access_token,
                refresh_token_encrypted=token_resp.refresh_token,
                token_type=token_resp.token_type,
                expires_at=expires_at,
                refresh_expires_at=refresh_expires_at,
                scope=token_resp.scope,
                is_current=True,
                rotation_version=1,
            )
        )

        external_id = None
        display = connection.display_name
        region = None
        try:
            gateway = EbayApiGateway(environment=st.environment, http=self.http)
            summary = await gateway.get_user_account_summary(token_resp.access_token)
            external_id = str(summary.get("user_id") or summary.get("username") or "") or None
            display = str(summary.get("username") or display or "eBay account")
            region = summary.get("registration_marketplace_id")
            await self.logs.add_api_log(
                MarketplaceApiLogModel(
                    connection_id=connection.id,
                    workspace_id=ctx.workspace_id,
                    channel=self.channel,
                    method="GET",
                    path="/commerce/identity/v1/user/",
                    status_code=200,
                    duration_ms=None,
                    success=True,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("ebay_identity_probe_failed", error=str(exc))
            await self.logs.add_api_log(
                MarketplaceApiLogModel(
                    connection_id=connection.id,
                    workspace_id=ctx.workspace_id,
                    channel=self.channel,
                    method="GET",
                    path="/commerce/identity/v1/user/",
                    status_code=None,
                    success=False,
                    error_code="IDENTITY_PROBE_FAILED",
                )
            )

        # Duplicate external account protection (same workspace)
        if external_id:
            existing = await self.connections.find_by_external(
                ctx.workspace_id, self.channel, external_id
            )
            if existing and existing.id != connection.id and existing.status == ConnectionStatus.CONNECTED:
                connection.status = ConnectionStatus.ERROR
                connection.last_error_code = "ALREADY_CONNECTED"
                connection.last_error_message = "This eBay account is already connected"
                await self.session.flush()
                raise MarketplaceAlreadyConnected(
                    "This eBay seller account is already connected to this workspace"
                )

        # First connected account becomes default
        existing_connected = [
            c
            for c in await self.connections.list_for_workspace(ctx.workspace_id, channel=self.channel)
            if c.status == ConnectionStatus.CONNECTED and c.id != connection.id
        ]
        if not existing_connected:
            connection.is_default = True

        connection.status = ConnectionStatus.CONNECTED
        connection.connected_at = datetime.now(UTC)
        connection.external_account_id = (
            external_id or connection.external_account_id or f"ebay:{connection.id.hex[:12]}"
        )
        connection.external_username = display
        connection.display_name = display
        connection.region = str(region) if region else connection.region
        connection.scopes = token_resp.scope
        connection.last_success_at = datetime.now(UTC)
        connection.last_validated_at = datetime.now(UTC)
        connection.last_refreshed_at = datetime.now(UTC)
        connection.last_error_at = None
        connection.last_error_code = None
        connection.last_error_message = None
        connection.disconnected_at = None
        connection.suspended_at = None
        meta = dict(connection.metadata_json or {})
        meta.update(
            {
                "token_type": token_resp.token_type,
                "environment": st.environment,
                "connected_via": "oauth_authorization_code",
            }
        )
        connection.metadata_json = meta

        await self.audit.add(
            event_type="marketplace.oauth.completed",
            message="eBay OAuth authorization completed",
            actor_user_id=ctx.user_id,
            workspace_id=ctx.workspace_id,
            metadata={
                "connection_id": str(connection.id),
                "external_account_id": connection.external_account_id,
                "environment": st.environment,
            },
        )
        await self.session.flush()
        logger.info("ebay_connect_completed", connection_id=str(connection.id))
        return OAuthCallbackResult(
            connection_id=connection.id,
            status=ConnectionStatus.CONNECTED,
            external_account_id=connection.external_account_id,
            display_name=connection.display_name,
        )

    async def disconnect(self, ctx: MarketplaceContext, connection_id: UUID) -> None:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None or connection.channel != self.channel:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")

        current = await self.tokens.get_current(connection_id)
        if current and current.refresh_token_encrypted:
            try:
                oauth = await self._oauth_client(ctx.workspace_id, connection.environment)
                await revoke_ebay_token(
                    oauth.config,
                    token=current.refresh_token_encrypted,
                    token_type_hint="refresh_token",
                    http=self.http,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("ebay_revoke_skipped", error=str(exc))

        await self.tokens.revoke_current(connection.id)
        was_default = connection.is_default
        connection.status = ConnectionStatus.DISCONNECTED
        connection.disconnected_at = datetime.now(UTC)
        connection.is_default = False
        await self.audit.add(
            event_type="marketplace.oauth.disconnected",
            message="eBay connection disconnected",
            actor_user_id=ctx.user_id,
            workspace_id=ctx.workspace_id,
            metadata={"connection_id": str(connection_id)},
        )
        if was_default:
            # promote another connected account if any
            others = [
                c
                for c in await self.connections.list_for_workspace(ctx.workspace_id, channel=self.channel)
                if c.id != connection_id and c.status == ConnectionStatus.CONNECTED
            ]
            if others:
                others[0].is_default = True
        await self.session.flush()
        logger.info("ebay_disconnected", connection_id=str(connection_id))

    async def refresh_token(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")

        acquired = await self.refresh_lock.acquire(connection_id)
        if not acquired:
            raise MarketplaceRefreshInProgress()

        try:
            current = await self.tokens.get_current(connection_id)
            if current is None or not current.refresh_token_encrypted:
                connection.status = ConnectionStatus.REAUTH_REQUIRED
                await self.logs.add_refresh_history(
                    MarketplaceTokenRefreshHistoryModel(
                        connection_id=connection_id,
                        success=False,
                        error_code="NO_REFRESH_TOKEN",
                        error_message="Missing refresh token",
                    )
                )
                await self.audit.add(
                    event_type="marketplace.oauth.refresh_failed",
                    message="Refresh failed: missing refresh token",
                    actor_user_id=ctx.user_id,
                    workspace_id=ctx.workspace_id,
                    metadata={"connection_id": str(connection_id)},
                )
                await self.session.flush()
                raise MarketplaceError(
                    "eBay refresh token missing; reauthorization required",
                    code="EBAY_REAUTH_REQUIRED",
                    provider="ebay",
                    retryable=False,
                )

            # Skip refresh if access token still valid with skew
            expires = current.expires_at
            if expires and expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires and expires > datetime.now(UTC) + timedelta(seconds=120):
                return {
                    "status": "not_needed",
                    "expires_at": expires.isoformat(),
                    "connection_id": str(connection_id),
                }

            try:
                oauth = await self._oauth_client(ctx.workspace_id, connection.environment)
                token_resp = await oauth.refresh(refresh_token=current.refresh_token_encrypted)
                await self.tokens.mark_all_not_current(connection_id)
                expires_at = (
                    datetime.now(UTC) + timedelta(seconds=int(token_resp.expires_in))
                    if token_resp.expires_in
                    else None
                )
                await self.tokens.add(
                    MarketplaceOAuthTokenModel(
                        connection_id=connection_id,
                        access_token_encrypted=token_resp.access_token,
                        refresh_token_encrypted=token_resp.refresh_token
                        or current.refresh_token_encrypted,
                        token_type=token_resp.token_type,
                        expires_at=expires_at,
                        scope=token_resp.scope or current.scope,
                        is_current=True,
                        rotation_version=(current.rotation_version or 1) + 1,
                    )
                )
                current.revoked_at = datetime.now(UTC)
                connection.status = ConnectionStatus.CONNECTED
                connection.last_success_at = datetime.now(UTC)
                connection.last_refreshed_at = datetime.now(UTC)
                connection.last_error_at = None
                connection.last_error_code = None
                connection.last_error_message = None
                await self.logs.add_refresh_history(
                    MarketplaceTokenRefreshHistoryModel(connection_id=connection_id, success=True)
                )
                await self.audit.add(
                    event_type="marketplace.oauth.refresh_succeeded",
                    message="eBay access token refreshed",
                    actor_user_id=ctx.user_id,
                    workspace_id=ctx.workspace_id,
                    metadata={"connection_id": str(connection_id)},
                )
                await self.session.flush()
                return {
                    "status": "refreshed",
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "connection_id": str(connection_id),
                }
            except MarketplaceError as exc:
                connection.status = ConnectionStatus.REAUTH_REQUIRED
                connection.last_error_at = datetime.now(UTC)
                connection.last_error_code = "REFRESH_FAILED"
                connection.last_error_message = str(exc)[:500]
                await self.logs.add_refresh_history(
                    MarketplaceTokenRefreshHistoryModel(
                        connection_id=connection_id,
                        success=False,
                        error_code="REFRESH_FAILED",
                        error_message=str(exc)[:500],
                    )
                )
                await self.audit.add(
                    event_type="marketplace.oauth.refresh_failed",
                    message="eBay token refresh failed",
                    actor_user_id=ctx.user_id,
                    workspace_id=ctx.workspace_id,
                    metadata={"connection_id": str(connection_id), "error": str(exc)[:300]},
                )
                await self.session.flush()
                raise TokenRefreshFailed(str(exc), cause=exc) from exc
            except Exception as exc:  # noqa: BLE001
                connection.status = ConnectionStatus.REAUTH_REQUIRED
                connection.last_error_at = datetime.now(UTC)
                connection.last_error_code = "REFRESH_FAILED"
                connection.last_error_message = str(exc)[:500]
                await self.logs.add_refresh_history(
                    MarketplaceTokenRefreshHistoryModel(
                        connection_id=connection_id,
                        success=False,
                        error_code="REFRESH_FAILED",
                        error_message=str(exc)[:500],
                    )
                )
                await self.session.flush()
                raise TokenRefreshFailed(str(exc), cause=exc) from exc
        finally:
            await self.refresh_lock.release(connection_id)

    async def validate_connection(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
        token = await self.tokens.get_current(connection_id)
        if token is None:
            return {
                "connection_id": str(connection_id),
                "status": connection.status,
                "valid": False,
                "reason": "no_token",
                "token_expired": True,
                "refresh_expired": True,
            }
        now = datetime.now(UTC)
        expires = token.expires_at
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        refresh_exp = token.refresh_expires_at
        if refresh_exp and refresh_exp.tzinfo is None:
            refresh_exp = refresh_exp.replace(tzinfo=UTC)
        access_expired = bool(expires and expires <= now)
        refresh_expired = bool(refresh_exp and refresh_exp <= now)
        expiring_soon = bool(expires and now < expires <= now + timedelta(minutes=10))

        identity_ok = None
        if connection.status == ConnectionStatus.CONNECTED and not access_expired:
            try:
                gateway = EbayApiGateway(environment=connection.environment, http=self.http)
                summary = await gateway.get_user_account_summary(token.access_token_encrypted)
                identity_ok = True
                if summary.get("username"):
                    connection.external_username = str(summary["username"])
                if summary.get("user_id"):
                    connection.external_account_id = str(summary["user_id"])
                connection.last_validated_at = now
                connection.last_success_at = now
            except Exception as exc:  # noqa: BLE001
                identity_ok = False
                logger.warning("ebay_validate_identity_failed", error=str(exc))
                if "401" in str(exc) or "UNAUTHORIZED" in str(exc).upper():
                    connection.status = ConnectionStatus.REAUTH_REQUIRED

        valid = (
            connection.status == ConnectionStatus.CONNECTED
            and not access_expired
            and not refresh_expired
            and identity_ok is not False
        )
        await self.session.flush()
        return {
            "connection_id": str(connection_id),
            "status": connection.status,
            "valid": valid,
            "token_expired": access_expired,
            "token_expiring_soon": expiring_soon,
            "refresh_expired": refresh_expired,
            "identity_ok": identity_ok,
            "environment": connection.environment,
            "external_account_id": connection.external_account_id,
            "is_default": connection.is_default,
            "region": connection.region,
        }

    async def set_default(self, ctx: MarketplaceContext, connection_id: UUID) -> MarketplaceConnectionModel:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None or connection.channel != self.channel:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
        if connection.status != ConnectionStatus.CONNECTED:
            raise ValidationAppError(
                "Only connected accounts can be default",
                details=[{"field": "status", "issue": connection.status}],
            )
        await self.connections.clear_default(ctx.workspace_id, self.channel)
        connection.is_default = True
        await self.audit.add(
            event_type="marketplace.connection.default_set",
            message="Default eBay connection updated",
            actor_user_id=ctx.user_id,
            workspace_id=ctx.workspace_id,
            metadata={"connection_id": str(connection_id)},
        )
        await self.session.flush()
        return connection

    async def suspend(self, ctx: MarketplaceContext, connection_id: UUID) -> MarketplaceConnectionModel:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
        connection.status = ConnectionStatus.SUSPENDED
        connection.suspended_at = datetime.now(UTC)
        await self.session.flush()
        return connection

    async def resume(self, ctx: MarketplaceContext, connection_id: UUID) -> MarketplaceConnectionModel:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
        token = await self.tokens.get_current(connection_id)
        connection.status = (
            ConnectionStatus.CONNECTED if token else ConnectionStatus.REAUTH_REQUIRED
        )
        connection.suspended_at = None
        await self.session.flush()
        return connection
