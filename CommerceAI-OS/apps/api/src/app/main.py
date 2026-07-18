"""ASGI entrypoint for CommerceAI OS API."""

from __future__ import annotations

import uvicorn

from app.bootstrap.factory import create_app
from app.config.settings import get_settings

app = create_app()


def run() -> None:
    """CLI entry: `commerceai-api` or `python -m app.main`."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug and not settings.is_production,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
