"""Celery application factory — task registration happens in app.tasks."""

from __future__ import annotations

from celery import Celery

from app.config.settings import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        settings.app_name,
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_always_eager=settings.celery_task_always_eager,
        task_eager_propagates=True,
        task_default_queue="commerceai.default",
        task_routes={
            "app.tasks.ai.*": {"queue": "commerceai.ai"},
            "app.tasks.marketplace.*": {"queue": "commerceai.marketplace"},
        },
    )
    return app


celery_app = create_celery_app()
