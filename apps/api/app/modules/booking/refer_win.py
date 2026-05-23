"""Public Refer & Win — CRM lead capture (loyalty points via Membership & Rewards)."""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import BadRequestException
from app.modules.booking.crm_link import resolve_customer_for_booking
from app.modules.crm.models import Customer
from app.modules.crm.pipeline_service import ensure_default_pipeline
from app.modules.leads.models import Lead
from app.modules.tenants.models import Tenant


class ReferWinSubmitBody(BaseModel):
    referral_name: str = Field(min_length=1, max_length=200)
    referral_phone: str = Field(min_length=3, max_length=50)
    referred_phone: str = Field(min_length=3, max_length=50)
    referred_email: str | None = None
    referral_reason: str = Field(min_length=1, max_length=2000)


def _split_referred_name(email: str | None, phone: str) -> tuple[str, str | None]:
    if email and "@" in email:
        local = email.split("@")[0].replace(".", " ").replace("_", " ")
        parts = local.split(maxsplit=1)
        if len(parts) == 2:
            return parts[0].title(), parts[1].title()
        return parts[0].title() if parts else "Referred", None
    return "Referred", phone[-4:] if phone else None


async def submit_refer_win(
    db: AsyncSession,
    tenant: Tenant,
    body: ReferWinSubmitBody,
) -> dict[str, Any]:
    referrer_id = await resolve_customer_for_booking(
        db,
        tenant.id,
        customer_id=None,
        customer_name=body.referral_name.strip(),
        customer_email=None,
        customer_phone=body.referral_phone.strip(),
        channel="refer_win",
    )
    if not referrer_id:
        raise BadRequestException("Could not save referrer")

    referrer = (
        await db.execute(
            select(Customer).where(Customer.id == referrer_id, Customer.tenant_id == tenant.id)
        )
    ).scalar_one()

    pipeline = await ensure_default_pipeline(db, tenant.id)
    new_stage = next((s for s in pipeline.stages if s.name == "New"), None)
    if not new_stage and pipeline.stages:
        new_stage = sorted(pipeline.stages, key=lambda s: s.position)[0]

    first, last = _split_referred_name(body.referred_email, body.referred_phone)
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        pipeline_id=pipeline.id if pipeline else None,
        stage_id=new_stage.id if new_stage else None,
        first_name=first,
        last_name=last,
        email=(body.referred_email or "").strip() or None,
        phone=body.referred_phone.strip(),
        message=body.referral_reason.strip(),
        source="refer_win_qr",
        status="new",
        extra_data={
            "referrer_customer_id": str(referrer_id),
            "referral_name": body.referral_name.strip(),
            "referral_phone": body.referral_phone.strip(),
        },
    )
    db.add(lead)

    referrer.ref_count = int(getattr(referrer, "ref_count", 0) or 0) + 1
    db.add(referrer)

    await log_action(
        db,
        action="refer_win.submitted",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant.id,
        metadata={"referrer_customer_id": str(referrer_id)},
    )
    await db.commit()
    await db.refresh(lead)

    from app.workers.queue import enqueue

    await enqueue(
        "trigger_automation_for_event",
        tenant_id=str(tenant.id),
        event="lead_created",
        entity_id=str(lead.id),
        entity_type="lead",
    )

    from app.modules.membership_rewards.hooks import on_refer_win_submitted

    await on_refer_win_submitted(
        db,
        tenant_id=tenant.id,
        referrer_customer_id=referrer_id,
        lead_id=lead.id,
    )

    return {
        "lead_id": str(lead.id),
        "referrer_customer_id": str(referrer_id),
        "ref_count": referrer.ref_count,
        "message": "Thank you — your referral has been received.",
    }
