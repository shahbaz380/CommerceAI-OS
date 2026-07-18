"""OpenTelemetry bootstrap — optional via OTEL_ENABLED."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.settings import AppSettings
from app.infrastructure.logging.setup import get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger("app")

_tracer_provider = None


def setup_telemetry(settings: AppSettings) -> None:
    """Initialize tracer provider when enabled."""
    global _tracer_provider
    if not settings.otel_enabled:
        logger.info("otel_disabled")
        return

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": str(settings.app_env),
        }
    )
    provider = TracerProvider(resource=resource)

    endpoint = settings.otel_exporter_otlp_endpoint
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    logger.info("otel_enabled", endpoint=endpoint or "console")


def instrument_app(app: FastAPI, settings: AppSettings) -> None:
    """Attach FastAPI instrumentation when OTEL is enabled."""
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("otel_fastapi_instrumented")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("otel_fastapi_instrument_failed", error=str(exc))


def shutdown_telemetry() -> None:
    global _tracer_provider
    if _tracer_provider is not None:
        _tracer_provider.shutdown()
        _tracer_provider = None
