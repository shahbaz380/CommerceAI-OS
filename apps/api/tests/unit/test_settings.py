"""Settings loader tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import AppEnvironment, AppSettings, clear_settings_cache


def test_default_settings_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    clear_settings_cache()
    s = AppSettings()
    assert s.app_env == AppEnvironment.LOCAL
    assert s.api_prefix == "/api/v1"


def test_cors_csv_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    s = AppSettings()
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_production_rejects_weak_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "change-me")
    with pytest.raises(ValidationError):
        AppSettings()
