"""Public Refer & Win submissions — CRM leads, customers, referral rewards."""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import BadRequestException
from app.modules.booking.crm_link import resolve_customer_for_booking
from app.modules.crm.models import Customer
from app.modules.crm.pipeline_service import ensure_default_pipeline
from app.modules.leads.models import Lead
from app.modules.referrals.models import ReferralProgram
from app.modules.tenants.models import Tenant


class ReferWinSubmitBody(BaseModel):
    referral_name: str = Field(min_length=1, max_length=200)
    referral_phone: str = Field(min_length=3, max_length=50)
    referred_phone: str = Field(min_length=3, max_length=50)
    referred_email: str | None = None
    referral_reason: str = Field(min_length=1, max_length=2000)


async def resolve_active_tenant_referral_program(
    db: AsyncSession, tenant_id: uuid.UUID
) -> ReferralProgram | None:
    programs = (
        await db.execute(
            select(ReferralProgram)
            .where(
                ReferralProgram.type == "tradesman",
                ReferralProgram.status == "approved",
            )
            .order_by(desc(ReferralProgram.created_at))
        )
    ).scalars().all()
    for prog in programs:
        rules = prog.rules or {}
        if str(rules.get("tenant_id")) != str(tenant_id):
            continue
        if rules.get("activation_status") == "inactive":
            continue
        return prog
    return None


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

    program = await resolve_active_tenant_referral_program(db, tenant.id)
    referrer.ref_count = int(getattr(referrer, "ref_count", 0) or 0) + 1
    if program:
        referrer.referral_program_id = program.id
        referrer.reward_amount = float(program.reward_amount)
        referrer.reward_type = program.reward_type
        referrer.reward_delivery_method = program.reward_delivery_method
    db.add(referrer)

    await log_action(
        db,
        action="refer_win.submitted",
        resource="lead",
        resource_id=lead.id,
        tenant_id=tenant.id,
        metadata={
            "referrer_customer_id": str(referrer_id),
            "referral_program_id": str(program.id) if program else None,
        },
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

    return {
        "lead_id": str(lead.id),
        "referrer_customer_id": str(referrer_id),
        "ref_count": referrer.ref_count,
        "reward": {
            "program_id": str(program.id),
            "amount": float(referrer.reward_amount) if referrer.reward_amount is not None else None,
            "type": referrer.reward_type,
            "delivery_method": referrer.reward_delivery_method,
        }
        if program
        else None,
        "message": "Thank you — your referral has been received.",
    }
