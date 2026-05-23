"""
Webhook router.

All inbound webhooks verify their provider's signature before doing any work.
Unverified or replayed requests are rejected with 401/400 *without* enqueuing
any jobs or mutating state.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Reject Svix signatures with a timestamp older than this (replay protection).
_SVIX_MAX_AGE_SECONDS = 5 * 60


# ──────────────────────────────────────────────────────────────────────────
# Twilio
# ──────────────────────────────────────────────────────────────────────────

def _verify_twilio_signature(
    auth_token: str,
    url: str,
    form_params: dict[str, str],
    signature: str,
) -> bool:
    """
    Twilio signs `url + sorted(key + value for each form field)` with HMAC-SHA1
    keyed by the account auth_token, then base64-encodes it.

    Reference:
    https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    if not auth_token or not signature:
        return False
    payload = url + "".join(f"{k}{form_params[k]}" for k in sorted(form_params.keys()))
    mac = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1)
    expected = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def _twilio_full_url(request: Request) -> str:
    """
    Build the full URL Twilio used to call us. Twilio signs the exact URL it
    posted to, including scheme + host + path + query, and *not* through the
    proxy. We honour TWILIO_WEBHOOK_BASE_URL when set so we sign against the
    public URL Caddy received rather than the internal one FastAPI sees.
    """
    if settings.TWILIO_WEBHOOK_BASE_URL:
        base = settings.TWILIO_WEBHOOK_BASE_URL.rstrip("/")
        return f"{base}{request.url.path}" + (f"?{request.url.query}" if request.url.query else "")
    return str(request.url)


async def _enforce_twilio_signature(request: Request) -> dict[str, str]:
    """Reject the request unless the X-Twilio-Signature header validates."""
    if not settings.TWILIO_AUTH_TOKEN:
        # In mock mode we don't expect Twilio calls — but if someone hits this
        # endpoint without credentials configured, refuse loudly.
        raise HTTPException(status_code=503, detail="Twilio webhooks not configured")

    signature = request.headers.get("X-Twilio-Signature", "")
    form = await request.form()
    form_dict = {k: str(v) for k, v in form.items()}

    url = _twilio_full_url(request)
    if not _verify_twilio_signature(
        settings.TWILIO_AUTH_TOKEN, url, form_dict, signature
    ):
        logger.warning(
            "Rejected Twilio webhook: signature mismatch url=%s sig=%s",
            url, signature[:16] + "..." if signature else "(none)",
        )
        raise HTTPException(status_code=401, detail="Invalid Twilio signature")

    return form_dict


# ──────────────────────────────────────────────────────────────────────────
# Resend (Svix)
# ──────────────────────────────────────────────────────────────────────────

def _verify_svix_signature(
    secret: str,
    msg_id: str,
    timestamp: str,
    body: bytes,
    signature_header: str,
) -> bool:
    """
    Svix (used by Resend) signs `${id}.${timestamp}.${body}` with HMAC-SHA256
    keyed by the base64-decoded portion after the `whsec_` prefix.

    Multiple comma-separated signatures are allowed (rotation). At least one
    must match. We also enforce a max age on the timestamp to defeat replays.
    """
    if not secret or not signature_header or not msg_id or not timestamp:
        return False

    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(int(datetime.now(timezone.utc).timestamp()) - ts) > _SVIX_MAX_AGE_SECONDS:
        return False

    secret_bytes = secret.split("_", 1)[-1] if secret.startswith("whsec_") else secret
    try:
        key = base64.b64decode(secret_bytes)
    except Exception:
        return False

    signed = f"{msg_id}.{timestamp}.".encode("utf-8") + body
    expected = base64.b64encode(
        hmac.new(key, signed, hashlib.sha256).digest()
    ).decode("utf-8")

    # Header format: "v1,<sig> v1,<sig2>" — space-delimited entries.
    for entry in signature_header.split(" "):
        _, _, candidate = entry.partition(",")
        if candidate and hmac.compare_digest(candidate, expected):
            return True
    return False


# ──────────────────────────────────────────────────────────────────────────
# Stripe
# ──────────────────────────────────────────────────────────────────────────

@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook — signature verified via the payment adapter."""
    from app.adapters import get_payment_adapter
    from app.workers.queue import enqueue

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        adapter = get_payment_adapter()
        event = await adapter.verify_webhook(payload, sig)
    except Exception as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        return Response(status_code=400, content="invalid signature")

    event_type = event.get("type", "")
    data_obj = event.get("data", {}).get("object", {}) or {}

    logger.info("Stripe event received: type=%s id=%s", event_type, event.get("id"))

    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "customer.subscription.trial_will_end",
    ):
        sub_id = data_obj.get("id")
        if sub_id:
            await enqueue("sync_stripe_subscription", stripe_subscription_id=sub_id)

    elif event_type == "invoice.payment_succeeded":
        await _record_stripe_invoice(db, data_obj, status_override="paid")

    elif event_type == "invoice.payment_failed":
        await _record_stripe_invoice(db, data_obj, status_override="payment_failed")

    elif event_type == "checkout.session.completed":
        metadata = data_obj.get("metadata") or {}
        if metadata.get("feature_code") == "accounting" and metadata.get("tenant_id"):
            import uuid as _uuid
            from app.modules.accounting import service as accounting_service

            await accounting_service.activate_from_checkout_metadata(
                db,
                tenant_id=_uuid.UUID(metadata["tenant_id"]),
                checkout_session_id=data_obj.get("id"),
            )
        else:
            sub_id = data_obj.get("subscription")
            if sub_id:
                await enqueue("sync_stripe_subscription", stripe_subscription_id=sub_id)

    elif event_type == "payment_intent.succeeded":
        meta = data_obj.get("metadata") or {}
        if meta.get("purpose") == "invoice_payment" and meta.get("invoice_id") and meta.get("tenant_id"):
            import uuid as _uuid
            from app.modules.accounting import service as accounting_service

            await accounting_service.apply_invoice_payment(
                db,
                tenant_id=_uuid.UUID(meta["tenant_id"]),
                invoice_id=_uuid.UUID(meta["invoice_id"]),
                amount_pence=int(data_obj.get("amount_received") or data_obj.get("amount") or 0),
                method="stripe",
                stripe_payment_intent_id=data_obj.get("id"),
            )

    return {"received": True}


async def _record_stripe_invoice(
    db: AsyncSession, invoice_data: dict, status_override: str | None = None
) -> None:
    """Upsert a Stripe billing_invoice row keyed by stripe_invoice_id."""
    from app.modules.billing.models import BillingInvoice, Subscription
    import uuid

    stripe_invoice_id = invoice_data.get("id")
    if not stripe_invoice_id:
        return

    # Resolve tenant via the customer's subscription record.
    stripe_customer_id = invoice_data.get("customer")
    stripe_subscription_id = invoice_data.get("subscription")
    tenant_id = None
    if stripe_subscription_id:
        sub = (
            await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_subscription_id
                )
            )
        ).scalar_one_or_none()
        if sub:
            tenant_id = sub.tenant_id
    if tenant_id is None and stripe_customer_id:
        sub = (
            await db.execute(
                select(Subscription).where(
                    Subscription.stripe_customer_id == stripe_customer_id
                )
            )
        ).scalar_one_or_none()
        if sub:
            tenant_id = sub.tenant_id

    if tenant_id is None:
        logger.warning(
            "Stripe invoice received but no subscription matched: invoice=%s customer=%s",
            stripe_invoice_id, stripe_customer_id,
        )
        return

    existing = (
        await db.execute(
            select(BillingInvoice).where(BillingInvoice.stripe_invoice_id == stripe_invoice_id)
        )
    ).scalar_one_or_none()

    amount_pence = int(invoice_data.get("amount_paid") or invoice_data.get("amount_due") or 0)
    status = status_override or invoice_data.get("status") or "open"
    invoice_pdf_url = invoice_data.get("invoice_pdf") or invoice_data.get("hosted_invoice_url")
    period_start = invoice_data.get("period_start")
    period_end = invoice_data.get("period_end")

    def _ts(v):
        if v is None:
            return None
        try:
            return datetime.fromtimestamp(int(v), tz=timezone.utc)
        except Exception:
            return None

    if existing:
        existing.amount_pence = amount_pence
        existing.status = status
        existing.invoice_pdf_url = invoice_pdf_url
        if period_start:
            existing.period_start = _ts(period_start)
        if period_end:
            existing.period_end = _ts(period_end)
        db.add(existing)
    else:
        db.add(BillingInvoice(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            stripe_invoice_id=stripe_invoice_id,
            amount_pence=amount_pence,
            currency=invoice_data.get("currency", "gbp"),
            status=status,
            invoice_pdf_url=invoice_pdf_url,
            period_start=_ts(period_start),
            period_end=_ts(period_end),
        ))

    await db.commit()


# ──────────────────────────────────────────────────────────────────────────
# Twilio inbound
# ──────────────────────────────────────────────────────────────────────────

@router.post("/twilio/sms")
async def twilio_sms_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle inbound SMS from Twilio. Signature MUST be valid."""
    form = await _enforce_twilio_signature(request)

    from_number = form.get("From", "")
    to_number = form.get("To", "")
    body = form.get("Body", "")
    sid = form.get("MessageSid", "")

    tenant_id = await _resolve_tenant_by_inbound_number(db, to_number)
    if not tenant_id:
        logger.warning("No tenant matched for inbound SMS to=%s", to_number)
        # Still 200 so Twilio doesn't retry — we logged it for ops.
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml",
        )

    from app.workers.queue import enqueue
    await enqueue(
        "process_inbound_sms",
        from_number=from_number,
        body=body,
        tenant_id=str(tenant_id),
        twilio_sid=sid,
    )

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle missed call from Twilio — create lead + send SMS."""
    form = await _enforce_twilio_signature(request)

    from_number = form.get("From", "")
    to_number = form.get("To", "")

    tenant_id = await _resolve_tenant_by_inbound_number(db, to_number)
    if from_number and tenant_id:
        from app.workers.queue import enqueue
        await enqueue(
            "handle_missed_call",
            from_number=from_number,
            to_number=to_number,
            tenant_id=str(tenant_id),
        )

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Sorry we missed your call. We will text you shortly.</Say></Response>',
        media_type="application/xml",
    )


async def _resolve_tenant_by_inbound_number(db: AsyncSession, to_number: str):
    """
    Resolve a tenant from the destination phone number.

    For now we match against `tenants.phone`. Production deployments with
    multiple numbers per tenant should switch to a `phone_routes` table.
    """
    if not to_number:
        return None
    from app.modules.tenants.models import Tenant
    normalised = to_number.strip()
    result = await db.execute(select(Tenant).where(Tenant.phone == normalised))
    tenant = result.scalar_one_or_none()
    return tenant.id if tenant else None


# ──────────────────────────────────────────────────────────────────────────
# Resend (email delivery events)
# ──────────────────────────────────────────────────────────────────────────

@router.post("/resend")
async def resend_webhook(
    request: Request,
    svix_id: str = Header(default="", alias="svix-id"),
    svix_timestamp: str = Header(default="", alias="svix-timestamp"),
    svix_signature: str = Header(default="", alias="svix-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Update outbound message delivery status from Resend events."""
    body = await request.body()
    if not _verify_svix_signature(
        settings.RESEND_WEBHOOK_SECRET, svix_id, svix_timestamp, body, svix_signature
    ):
        logger.warning("Rejected Resend webhook: invalid Svix signature id=%s", svix_id)
        raise HTTPException(status_code=401, detail="Invalid signature")

    import orjson
    try:
        event = orjson.loads(body)
    except orjson.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = (event.get("type") or "").lower()
    data = event.get("data") or {}
    email_id = data.get("email_id") or data.get("id")

    status_map = {
        "email.sent": "sent",
        "email.delivered": "delivered",
        "email.delivery_delayed": "delayed",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.opened": "opened",
        "email.clicked": "clicked",
    }
    new_status = status_map.get(event_type)
    if new_status and email_id:
        from sqlalchemy import update
        from app.modules.messaging.models import Message
        await db.execute(
            update(Message)
            .where(Message.provider_message_id == email_id)
            .values(status=new_status)
        )
        await db.commit()

    return {"received": True}
