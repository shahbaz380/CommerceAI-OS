"""Structured logging initialization (structlog + stdlib).

Supports application, API, security, AI, and audit logger names.
JSON in production; pretty console for local/dev.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config.settings import AppSettings


def setup_logging(settings: AppSettings) -> None:
    """Configure process-wide structured logging."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _add_service_fields(settings),
    ]

    if settings.use_json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Named loggers used across the platform
    for name in (
        "app",
        "app.api",
        "app.security",
        "app.ai",
        "app.audit",
        "app.marketplace",
        "uvicorn.access",
    ):
        logging.getLogger(name).setLevel(level)


def _add_service_fields(settings: AppSettings) -> structlog.types.Processor:
    def processor(
        logger: logging.Logger,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        event_dict.setdefault("service", settings.otel_service_name or settings.app_name)
        event_dict.setdefault("env", str(settings.app_env))
        event_dict.setdefault("version", settings.app_version)
        return event_dict

    return processor


def bind_request_context(
    *,
    request_id: str,
    correlation_id: str,
    workspace_id: str | None = None,
    path: str | None = None,
    method: str | None = None,
) -> None:
    """Bind request-scoped fields into structlog contextvars."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        correlation_id=correlation_id,
        workspace_id=workspace_id,
        path=path,
        method=method,
    )


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()


def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
