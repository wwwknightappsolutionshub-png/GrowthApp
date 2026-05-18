"""Re-export the email adapter factory so `from app.adapters.email import get_email_adapter` works."""
from app.adapters import get_email_adapter  # noqa: F401

__all__ = ["get_email_adapter"]
