"""Production-safety validator on Settings."""
import os
import pytest

from app.core.config import Settings


def _base_env(monkeypatch, **overrides) -> None:
    """Helper: clear vars then set the supplied ones."""
    keys = [
        "ENVIRONMENT", "JWT_SECRET", "JWT_REFRESH_SECRET", "DATABASE_URL",
        "ALLOWED_ORIGINS", "PAYMENT_PROVIDER", "STRIPE_WEBHOOK_SECRET",
        "SMS_PROVIDER", "TWILIO_AUTH_TOKEN",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    for k, v in overrides.items():
        monkeypatch.setenv(k, v)


def test_production_rejects_placeholder_jwt_secret(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="local_dev_secret_change_in_production",
        JWT_REFRESH_SECRET="x" * 64,
        DATABASE_URL="postgresql+asyncpg://u:p@db/customerflow_ai",
        ALLOWED_ORIGINS="https://app.example.com",
    )
    with pytest.raises(ValueError) as ei:
        Settings()
    assert "JWT_SECRET" in str(ei.value)


def test_production_rejects_short_secrets(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="short",
        JWT_REFRESH_SECRET="x" * 64,
        DATABASE_URL="postgresql+asyncpg://u:p@db/customerflow_ai",
        ALLOWED_ORIGINS="https://app.example.com",
    )
    with pytest.raises(ValueError) as ei:
        Settings()
    assert "at least 32" in str(ei.value)


def test_production_rejects_sqlite(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="a" * 64,
        JWT_REFRESH_SECRET="b" * 64,
        DATABASE_URL="sqlite+aiosqlite:///./prod.db",
        ALLOWED_ORIGINS="https://app.example.com",
    )
    with pytest.raises(ValueError) as ei:
        Settings()
    assert "SQLite" in str(ei.value)


def test_production_rejects_stripe_without_webhook_secret(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="a" * 64,
        JWT_REFRESH_SECRET="b" * 64,
        DATABASE_URL="postgresql+asyncpg://u:p@db/customerflow_ai",
        ALLOWED_ORIGINS="https://app.example.com",
        PAYMENT_PROVIDER="stripe",
    )
    with pytest.raises(ValueError) as ei:
        Settings()
    assert "STRIPE_WEBHOOK_SECRET" in str(ei.value)


def test_production_rejects_twilio_without_auth_token(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="a" * 64,
        JWT_REFRESH_SECRET="b" * 64,
        DATABASE_URL="postgresql+asyncpg://u:p@db/customerflow_ai",
        ALLOWED_ORIGINS="https://app.example.com",
        SMS_PROVIDER="twilio",
    )
    with pytest.raises(ValueError) as ei:
        Settings()
    assert "TWILIO_AUTH_TOKEN" in str(ei.value)


def test_production_accepts_strong_config(monkeypatch):
    _base_env(
        monkeypatch,
        ENVIRONMENT="production",
        JWT_SECRET="a" * 64,
        JWT_REFRESH_SECRET="b" * 64,
        DATABASE_URL="postgresql+asyncpg://u:p@db/customerflow_ai",
        ALLOWED_ORIGINS="https://app.example.com",
    )
    s = Settings()
    assert s.is_production is True


def test_non_production_accepts_dev_defaults(monkeypatch):
    _base_env(monkeypatch, ENVIRONMENT="development")
    s = Settings()
    assert s.is_production is False
