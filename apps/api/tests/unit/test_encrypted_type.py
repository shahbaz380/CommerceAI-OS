"""EncryptedString type foundation tests."""

from __future__ import annotations

from app.infrastructure.database.types.encrypted import EncryptedString


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key-with-32bytes-min!!")
    from app.config.settings import clear_settings_cache

    clear_settings_cache()
    # Reset fernet cache
    import app.infrastructure.database.types.encrypted as enc_mod

    enc_mod._fernet = None
    enc_mod._fernet_init = False

    col = EncryptedString()
    bound = col.process_bind_param("sensitive-token", dialect=type("D", (), {"name": "postgresql"})())
    assert isinstance(bound, bytes)
    assert not bound.decode("utf-8", errors="ignore").startswith("sensitive")
    plain = col.process_result_value(bound, dialect=type("D", (), {"name": "postgresql"})())
    assert plain == "sensitive-token"
    clear_settings_cache()
