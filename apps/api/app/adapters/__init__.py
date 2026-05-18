"""
Adapter factory — returns the right implementation based on PROVIDER env vars.
"""
from functools import lru_cache
from app.core.config import settings


@lru_cache
def get_sms_adapter():
    from app.adapters.sms.base import SMSAdapter
    if settings.SMS_PROVIDER == "twilio":
        from app.adapters.sms.twilio import TwilioSMSAdapter
        return TwilioSMSAdapter()
    from app.adapters.sms.mock import MockSMSAdapter
    return MockSMSAdapter()


@lru_cache
def get_email_adapter():
    if settings.EMAIL_PROVIDER == "resend":
        from app.adapters.email.resend import ResendEmailAdapter
        return ResendEmailAdapter(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.RESEND_FROM_EMAIL,
            from_name=settings.RESEND_FROM_NAME,
        )
    from app.adapters.email.mock import MockEmailAdapter
    return MockEmailAdapter()


@lru_cache
def get_payment_adapter():
    if settings.PAYMENT_PROVIDER == "stripe":
        from app.adapters.payment.stripe import StripePaymentAdapter
        return StripePaymentAdapter()
    from app.adapters.payment.mock import MockPaymentAdapter
    return MockPaymentAdapter()


@lru_cache
def get_ai_adapter():
    if settings.AI_PROVIDER == "openai":
        from app.adapters.ai.openai import OpenAIAdapter
        return OpenAIAdapter()
    from app.adapters.ai.mock import MockAIAdapter
    return MockAIAdapter()


@lru_cache
def get_social_adapter():
    if settings.SOCIAL_PROVIDER == "facebook":
        from app.adapters.social.facebook import FacebookSocialAdapter
        return FacebookSocialAdapter()
    from app.adapters.social.mock import MockSocialAdapter
    return MockSocialAdapter()


@lru_cache
def get_whatsapp_adapter():
    if settings.WHATSAPP_PROVIDER == "twilio":
        from app.adapters.whatsapp.twilio import TwilioWhatsAppAdapter
        return TwilioWhatsAppAdapter()
    from app.adapters.whatsapp.mock import MockWhatsAppAdapter
    return MockWhatsAppAdapter()
