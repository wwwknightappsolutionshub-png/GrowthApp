from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Hard-coded list of placeholder values shipped in .env.example.
# Production refuses to boot if any of these are still set.
_PLACEHOLDER_SECRETS = frozenset({
    "local_dev_secret_change_in_production",
    "local_dev_refresh_secret_change_in_production",
    "change_me_with_openssl_rand_base64_32",
    "change_me_with_openssl_rand_base64_48",
    "change_me_strong_password",
    "change_me_redis_password",
    "build_secret",
    "",
})

_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    # Published tenant sites: https://{tenant_slug}.{BUSINESS_SITE_BASE_DOMAIN}
    BUSINESS_SITE_BASE_DOMAIN: str = "customerflowai.online"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    # Absolute URL the embeddable widget should POST back to. Falls back to a
    # relative /api/v1 if blank (works when the widget is hosted on the same
    # origin as the API).
    PUBLIC_API_BASE_URL: str = ""

    # Database - SQLite for local dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./customerflow_dev.db"

    # Redis - not required for local dev
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "local_dev_secret_change_in_production"
    JWT_REFRESH_SECRET: str = "local_dev_refresh_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Providers (mock | real)
    SMS_PROVIDER: Literal["mock", "twilio"] = "mock"
    EMAIL_PROVIDER: Literal["mock", "resend"] = "mock"
    PAYMENT_PROVIDER: Literal["mock", "stripe"] = "mock"
    AI_PROVIDER: Literal["mock", "openai"] = "mock"
    SOCIAL_PROVIDER: Literal["mock", "facebook"] = "mock"
    WHATSAPP_PROVIDER: Literal["mock", "twilio"] = "mock"

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    # WhatsApp business number (E.164). Defaults to TWILIO_FROM_NUMBER if unset.
    TWILIO_WHATSAPP_FROM_NUMBER: str = ""
    # Pre-approved template Content SID for first-contact messages.
    TWILIO_WHATSAPP_CONTENT_SID: str = ""
    # Public base URL Twilio uses to POST to us. Twilio signs the full URL it
    # called; set this to e.g. "https://api.yourdomain.com" so we can verify.
    TWILIO_WEBHOOK_BASE_URL: str = ""

    # Resend
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@example.com"
    RESEND_FROM_NAME: str = "CustomerFlow AI"
    # Resend uses Svix-style HMAC signatures on webhook bodies.
    RESEND_WEBHOOK_SECRET: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_GROWTH: str = ""
    STRIPE_PRICE_PRO: str = ""

    # Cookies (used for httpOnly access + refresh tokens)
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Hybrid AI router ─────────────────────────────────────────────────
    # Ordered list of providers the router will try, comma-separated.
    # First successful provider wins. e.g. "openai,anthropic,ollama".
    AI_PROVIDER_ORDER: str = "openai,ollama"
    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES_PER_PROVIDER: int = 1
    AI_ASSISTANT_SESSION_HOURS: int = 48
    AI_ASSISTANT_SAVE_WARNING_HOURS: int = 6

    # Anthropic (Claude) — optional second-priority fallback.
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    # Ollama — local LLM fallback. Free, no network egress, perfect for offline /
    # cost-controlled tenants. Default URL works for Docker desktop & VPS.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Pricing table (£ per 1M tokens) for cost tracking. Override per
    # deployment if your contract prices differ.
    AI_PRICE_GBP_INPUT_PER_MTOKEN_OPENAI: float = 0.12
    AI_PRICE_GBP_OUTPUT_PER_MTOKEN_OPENAI: float = 0.48
    AI_PRICE_GBP_INPUT_PER_MTOKEN_ANTHROPIC: float = 2.40
    AI_PRICE_GBP_OUTPUT_PER_MTOKEN_ANTHROPIC: float = 12.00
    AI_PRICE_GBP_INPUT_PER_MTOKEN_OLLAMA: float = 0.00
    AI_PRICE_GBP_OUTPUT_PER_MTOKEN_OLLAMA: float = 0.00

    @property
    def ai_provider_order_list(self) -> list[str]:
        return [p.strip() for p in self.AI_PROVIDER_ORDER.split(",") if p.strip()]

    # Facebook
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    # Google Business Profile (OAuth)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    INTEGRATIONS_TOKEN_ENCRYPTION_KEY: str = ""

    # Lead factory: scraped leads land on this tenant before marketplace + trial delivery
    MARKETPLACE_POOL_TENANT_SLUG: str = "lead-pool-system"
    TRIAL_LEAD_DAYS: int = 7
    TRIAL_LEADS_PER_DAY: int = 2

    # Sentry
    SENTRY_DSN: str = ""

    # Web Push / PWA notifications. Generate VAPID keys with:
    # python -m pywebpush --gen-vapid-keys
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@customerflow.ai"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    # ── Production safety guards ──────────────────────────────────────────
    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        """Refuse to boot in production with insecure defaults."""
        if self.ENVIRONMENT != "production":
            return self

        errors: list[str] = []

        for name in ("JWT_SECRET", "JWT_REFRESH_SECRET"):
            value = getattr(self, name)
            if value in _PLACEHOLDER_SECRETS:
                errors.append(f"{name} is a placeholder. Generate one with `python -c \"import secrets; print(secrets.token_hex(64))\"`.")
            elif len(value) < _MIN_SECRET_LENGTH:
                errors.append(f"{name} must be at least {_MIN_SECRET_LENGTH} characters in production.")

        if self.is_sqlite:
            errors.append("DATABASE_URL points at SQLite — production requires PostgreSQL.")

        if not self.ALLOWED_ORIGINS or "localhost" in self.ALLOWED_ORIGINS:
            errors.append("ALLOWED_ORIGINS must be set to your production frontend origin(s).")

        # Webhook secrets must be set if their providers are enabled
        if self.PAYMENT_PROVIDER == "stripe" and not self.STRIPE_WEBHOOK_SECRET:
            errors.append("STRIPE_WEBHOOK_SECRET is required when PAYMENT_PROVIDER=stripe.")
        if self.SMS_PROVIDER == "twilio" and not self.TWILIO_AUTH_TOKEN:
            errors.append("TWILIO_AUTH_TOKEN is required when SMS_PROVIDER=twilio (used for inbound webhook signature verification).")

        if errors:
            joined = "\n  - ".join(errors)
            raise ValueError(
                f"Refusing to start in production due to insecure configuration:\n  - {joined}\n"
                "Fix these in your .env file and restart."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
