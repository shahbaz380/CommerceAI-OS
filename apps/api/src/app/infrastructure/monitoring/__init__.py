"""OpenTelemetry and metrics placeholders."""

from app.infrastructure.monitoring.telemetry import instrument_app, setup_telemetry, shutdown_telemetry

__all__ = ["instrument_app", "setup_telemetry", "shutdown_telemetry"]
