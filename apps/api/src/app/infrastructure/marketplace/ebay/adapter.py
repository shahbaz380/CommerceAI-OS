"""eBay MarketplaceAdapter — OAuth connect/disconnect/refresh foundation."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.marketplaces.enums import ConnectionStatus, MarketplaceChannel, MarketplaceEnvironment
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.marketplace.base import (
    ConnectResult,
    MarketplaceAdapter,
    MarketplaceContext,
    OAuthCallbackResult,
)
from app.infrastructure.marketplace.ebay.client.gateway import EbayApiGateway
from app.infrastructure.marketplace.ebay.oauth.client import DEFAULT_EBAY_SCOPES, EbayOAuthClient, EbayOAuthConfig
from app.infrastructure.marketplace.http.client import AsyncHttpClient
from app.infrastructure.persistence.models.marketplace import (
    MarketplaceConnectionModel,
    MarketplaceOAuthStateModel,
    MarketplaceOAuthTokenModel,
    MarketplaceTokenRefreshHistoryModel,
)
from app.infrastructure.persistence.repositories.marketplace import (
    MarketplaceConnectionRepository,
    MarketplaceCredentialRepository,
    MarketplaceLogRepository,
    MarketplaceTokenRepository,
    OAuthStateRepository,
)
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
        self.states = OAuthStateRepository(session)
        self.logs = MarketplaceLogRepository(session)

    async def health(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "status": "ready",
            "capabilities": [
                "oauth.connect",
                "oauth.refresh",
                "oauth.disconnect",
                "connection.validate",
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
        config = EbayOAuthConfig(
            client_id=cred.client_id,
            client_secret=cred.client_secret_encrypted,
            redirect_uri=cred.redirect_uri,
            environment=environment,
            scopes=cred.scopes or DEFAULT_EBAY_SCOPES,
            ru_name=cred.ru_name,
        )
        return EbayOAuthClient(config, http=self.http)

    async def begin_connect(self, ctx: MarketplaceContext, **kwargs: Any) -> ConnectResult:
        if ctx.user_id is None:
            raise ValidationAppError(
                "user_id required to connect marketplace",
                details=[{"field": "user_id", "issue": "required"}],
            )
        environment = kwargs.get("environment") or ctx.environment or MarketplaceEnvironment.SANDBOX
        display_name = kwargs.get("display_name")
        oauth = await self._oauth_client(ctx.workspace_id, environment)

        connection = MarketplaceConnectionModel(
            workspace_id=ctx.workspace_id,
            channel=self.channel,
            environment=environment,
            status=ConnectionStatus.PENDING,
            display_name=display_name or "eBay account",
            connected_by_user_id=ctx.user_id,
        )
        await self.connections.add(connection)

        state = secrets.token_urlsafe(24)
        await self.states.add(
            MarketplaceOAuthStateModel(
                state=state,
                workspace_id=ctx.workspace_id,
                channel=self.channel,
                environment=environment,
                user_id=ctx.user_id,
                redirect_uri=oauth.config.redirect_uri,
                expires_at=datetime.now(UTC) + timedelta(minutes=15),
            )
        )
        url = oauth.build_authorization_url(state=state)
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
            state=state,
        )

    async def complete_connect(
        self,
        ctx: MarketplaceContext,
        *,
        code: str,
        state: str,
        **kwargs: Any,
    ) -> OAuthCallbackResult:
        st = await self.states.get_by_state(state)
        if st is None:
            raise ValidationAppError("Invalid OAuth state", code="OAUTH_STATE_INVALID")
        if st.consumed_at is not None:
            raise ValidationAppError("OAuth state already used", code="OAUTH_STATE_CONSUMED")
        exp = st.expires_at if st.expires_at.tzinfo else st.expires_at.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            raise ValidationAppError("OAuth state expired", code="OAUTH_STATE_EXPIRED")
        if st.workspace_id != ctx.workspace_id:
            raise ValidationAppError("OAuth state workspace mismatch", code="OAUTH_STATE_WORKSPACE")
        if st.channel != self.channel:
            raise ValidationAppError("OAuth state channel mismatch", code="OAUTH_STATE_CHANNEL")

        connection_id = kwargs.get("connection_id")
        connection = None
        if connection_id:
            connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            pending = [
                c
                for c in await self.connections.list_for_workspace(
                    ctx.workspace_id, channel=self.channel
                )
                if c.status == ConnectionStatus.PENDING and c.environment == st.environment
            ]
            connection = pending[0] if pending else None
        if connection is None:
            raise NotFoundError("Pending eBay connection not found", code="CONNECTION_NOT_FOUND")

        oauth = await self._oauth_client(ctx.workspace_id, st.environment)
        token_resp = await oauth.exchange_code(code=code)

        await self.tokens.mark_all_not_current(connection.id)
        expires_at = None
        if token_resp.expires_in:
            expires_at = datetime.now(UTC) + timedelta(seconds=int(token_resp.expires_in))
        refresh_expires_at = None
        if token_resp.refresh_token_expires_in:
            refresh_expires_at = datetime.now(UTC) + timedelta(
                seconds=int(token_resp.refresh_token_expires_in)
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
        try:
            gateway = EbayApiGateway(environment=st.environment, http=self.http)
            profile = await gateway.commerce_identity_user(token_resp.access_token)
            external_id = str(profile.get("userId") or profile.get("username") or "") or None
            display = str(profile.get("username") or display or "eBay account")
        except Exception as exc:  # noqa: BLE001
            logger.warning("ebay_identity_probe_failed", error=str(exc))

        connection.status = ConnectionStatus.CONNECTED
        connection.connected_at = datetime.now(UTC)
        connection.external_account_id = (
            external_id or connection.external_account_id or f"ebay:{connection.id.hex[:12]}"
        )
        connection.external_username = display
        connection.display_name = display
        connection.scopes = token_resp.scope
        connection.last_success_at = datetime.now(UTC)
        connection.last_error_at = None
        connection.last_error_code = None
        connection.last_error_message = None
        st.consumed_at = datetime.now(UTC)

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
        await self.tokens.revoke_current(connection.id)
        connection.status = ConnectionStatus.DISCONNECTED
        connection.disconnected_at = datetime.now(UTC)
        await self.session.flush()
        logger.info("ebay_disconnected", connection_id=str(connection_id))

    async def refresh_token(self, ctx: MarketplaceContext, connection_id: UUID) -> dict[str, Any]:
        connection = await self.connections.get_for_workspace(ctx.workspace_id, connection_id)
        if connection is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
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
            await self.session.flush()
            raise MarketplaceError(
                "eBay refresh token missing; reauthorization required",
                code="EBAY_REAUTH_REQUIRED",
                provider="ebay",
                retryable=False,
            )
        try:
            oauth = await self._oauth_client(ctx.workspace_id, connection.environment)
            token_resp = await oauth.refresh(refresh_token=current.refresh_token_encrypted)
            await self.tokens.mark_all_not_current(connection_id)
            expires_at = None
            if token_resp.expires_in:
                expires_at = datetime.now(UTC) + timedelta(seconds=int(token_resp.expires_in))
            await self.tokens.add(
                MarketplaceOAuthTokenModel(
                    connection_id=connection_id,
                    access_token_encrypted=token_resp.access_token,
                    refresh_token_encrypted=token_resp.refresh_token or current.refresh_token_encrypted,
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
            await self.logs.add_refresh_history(
                MarketplaceTokenRefreshHistoryModel(connection_id=connection_id, success=True)
            )
            await self.session.flush()
            return {
                "status": "refreshed",
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
        except MarketplaceError:
            raise
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
            raise MarketplaceError(
                "eBay token refresh failed",
                code="EBAY_REFRESH_FAILED",
                provider="ebay",
                retryable=True,
                cause=exc,
            ) from exc

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
            }
        expires = token.expires_at
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        expired = bool(expires and expires <= datetime.now(UTC))
        return {
            "connection_id": str(connection_id),
            "status": connection.status,
            "valid": connection.status == ConnectionStatus.CONNECTED and not expired,
            "token_expired": expired,
            "environment": connection.environment,
            "external_account_id": connection.external_account_id,
        }
