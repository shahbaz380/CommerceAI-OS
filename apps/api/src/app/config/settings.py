"""Pydantic Settings — configuration loader with env validation.

Supports APP_ENV: local | development | testing | staging | production
Secrets are read from environment / secret manager injection only.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from typing import Annotated


class AppEnvironment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


class AppSettings(BaseSettings):
    """Central application configuration.

    All fields may be overridden via environment variables.
    Nested env files are not required; use process env / .env for local.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = Field(default="commerceai-api", alias="APP_NAME")
    app_env: AppEnvironment = Field(default=AppEnvironment.LOCAL, alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    api_docs_enabled: bool = Field(default=True, alias="API_DOCS_ENABLED")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["*"],
        alias="ALLOWED_HOSTS",
    )

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: LogFormat = Field(default=LogFormat.JSON, alias="LOG_FORMAT")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://commerceai:commerceai@localhost:5432/commerceai_local",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=1800, alias="DATABASE_POOL_RECYCLE")
    database_startup_validate: bool = Field(default=False, alias="DATABASE_STARTUP_VALIDATE")
    database_startup_strict: bool = Field(default=False, alias="DATABASE_STARTUP_STRICT")

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_prefix: str = Field(default="commerceai:", alias="REDIS_PREFIX")

    # --- Celery ---
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        alias="CELERY_RESULT_BACKEND",
    )
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")

    # --- Security (placeholders; auth not implemented) ---
    secret_key: SecretStr = Field(
        default=SecretStr("change-me-to-a-long-random-string-min-32-chars"),
        alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # --- Rate limiting placeholder ---
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field(default="100/minute", alias="RATE_LIMIT_DEFAULT")

    # --- Multi-tenancy ---
    tenancy_enforcement: bool = Field(default=True, alias="TENANCY_ENFORCEMENT")
    default_tenant_header: str = Field(default="X-Workspace-Id", alias="DEFAULT_TENANT_HEADER")

    # --- Feature flags ---
    feature_ai_writes_enabled: bool = Field(default=False, alias="FEATURE_AI_WRITES_ENABLED")
    feature_ebay_sync_enabled: bool = Field(default=False, alias="FEATURE_EBAY_SYNC_ENABLED")
    feature_plugin_runtime: bool = Field(default=False, alias="FEATURE_PLUGIN_RUNTIME")
    feature_billing_enabled: bool = Field(default=False, alias="FEATURE_BILLING_ENABLED")

    # --- OpenTelemetry ---
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="commerceai-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_traces_sampler_arg: float = Field(default=1.0, alias="OTEL_TRACES_SAMPLER_ARG")

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                import json

                parsed = json.loads(raw)
                return [str(v) for v in parsed]
            return [part.strip() for part in raw.split(",") if part.strip()]
        raise TypeError("Expected list or comma-separated string")

    @model_validator(mode="after")
    def enforce_production_safety(self) -> AppSettings:
        if self.app_env == AppEnvironment.PRODUCTION:
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            secret = self.secret_key.get_secret_value()
            if secret.startswith("change-me") or len(secret) < 32:
                raise ValueError("SECRET_KEY must be a strong value in production (≥32 chars)")
            if self.api_docs_enabled and not self.debug:
                # Docs can be disabled explicitly in prod; warn via config not exception
                pass
        if self.app_env == AppEnvironment.TESTING:
            object.__setattr__(self, "celery_task_always_eager", True)
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.app_env == AppEnvironment.TESTING

    @property
    def use_json_logs(self) -> bool:
        return self.log_json or self.log_format == LogFormat.JSON or self.is_production

    def database_url_sync(self) -> str:
        """Sync URL for Alembic (asyncpg → psycopg/psycopg2 style placeholder)."""
        url = self.database_url
        return url.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Cached settings singleton for the process."""
    return AppSettings()


def clear_settings_cache() -> None:
    """Test helper to reload settings."""
    get_settings.cache_clear()
