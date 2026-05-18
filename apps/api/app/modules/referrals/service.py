"""Referral business logic — programs, links, events, payouts, hooks."""
from __future__ import annotations

import base64
import logging
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import Any

import segno
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.auth.models import User
from app.modules.billing.models import Subscription, SubscriptionPlan
from app.modules.booking.models import Booking
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Invoice
from app.modules.referrals.models import ReferralEvent, ReferralLink, ReferralPayout, ReferralProgram
from app.modules.tenants.models import TenantMember

logger = logging.getLogger(__name__)

EVENT_STATUSES = frozenset(
    {
        "clicked",
        "signed_up",
        "job_started",
        "job_completed",
        "invoice_paid",
        "eligible_for_reward",
        "reward_issued",
    }
)


def _frontend_base() -> str:
    return (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")


def _make_qr_data_url(ref_link: str) -> str:
    buf = BytesIO()
    segno.make(ref_link).save(buf, kind="png", scale=4)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


async def _unique_ref_code(db: AsyncSession) -> str:
    for _ in range(20):
        code = secrets.token_hex(5).upper()
        exists = (
            await db.execute(select(ReferralLink.id).where(ReferralLink.ref_code == code))
        ).scalar_one_or_none()
        if not exists:
            return code
    raise BadRequestException("Could not allocate referral code")


async def create_program(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID | None,
    type_: str,
    reward_amount: float,
    reward_type: str,
    reward_delivery_method: str,
    rules: dict,
) -> ReferralProgram:
    p = ReferralProgram(
        id=uuid.uuid4(),
        type=type_,
        owner_id=owner_id,
        reward_amount=Decimal(str(reward_amount)),
        reward_type=reward_type,
        reward_delivery_method=reward_delivery_method,
        rules=rules or {},
        status="disabled",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def get_program(db: AsyncSession, program_id: uuid.UUID) -> ReferralProgram:
    row = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == program_id))).scalar_one_or_none()
    if not row:
        raise NotFoundException("Referral program")
    return row


async def submit_for_approval(db: AsyncSession, program_id: uuid.UUID, actor_user_id: uuid.UUID) -> ReferralProgram:
    p = await get_program(db, program_id)
    if p.owner_id != actor_user_id:
        raise ForbiddenException("Not your program")
    p.status = "pending"
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def approve_program(
    db: AsyncSession,
    program_id: uuid.UUID,
    *,
    reward_amount: float | None,
    reason: str | None,
) -> ReferralProgram:
    p = await get_program(db, program_id)
    if reward_amount is not None:
        p.reward_amount = Decimal(str(reward_amount))
    rules = dict(p.rules or {})
    if reason is not None:
        rules["approval_override"] = {"reason": reason, "at": datetime.now(timezone.utc).isoformat()}
    p.rules = rules
    p.status = "approved"
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def reject_program(db: AsyncSession, program_id: uuid.UUID, reason: str | None) -> ReferralProgram:
    p = await get_program(db, program_id)
    rules = dict(p.rules or {})
    if reason:
        rules["rejection_reason"] = reason
    p.rules = rules
    p.status = "rejected"
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def ensure_can_generate_link(
    db: AsyncSession,
    *,
    program_id: uuid.UUID,
    acting_user_id: uuid.UUID,
    credentials: object | None,
    cookie_token: str | None,
) -> None:
    """Authorise link generation: global program active+approved; tradesman program approved and tenant member."""
    from app.core.dependencies import get_current_tenant

    prog = await get_program(db, program_id)
    if prog.status != "approved":
        raise BadRequestException("Program not approved")
    if prog.type == "global_saas":
        if (prog.rules or {}).get("activation_status") == "inactive":
            raise BadRequestException("Global referral program inactive")
        return
    tid = (prog.rules or {}).get("tenant_id")
    if not tid:
        raise BadRequestException("Program missing tenant_id")
    u, tenant, _role = await get_current_tenant(credentials, db, cookie_token)  # type: ignore[arg-type]
    if u.id != acting_user_id:
        raise ForbiddenException("Session user mismatch")
    if str(tenant.id) != str(tid):
        raise ForbiddenException("Not a member of this program's tenant")


async def generate_link(
    db: AsyncSession,
    *,
    program_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ReferralLink:
    await get_program(db, program_id)
    code = await _unique_ref_code(db)
    ref_link = f"{_frontend_base()}/r/{code}"
    qr = _make_qr_data_url(ref_link)
    link = ReferralLink(
        id=uuid.uuid4(),
        user_id=user_id,
        program_id=program_id,
        ref_code=code,
        ref_link=ref_link,
        qr_code_url=qr,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def list_links_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[ReferralLink]:
    return list(
        (
            await db.execute(select(ReferralLink).where(ReferralLink.user_id == user_id).order_by(ReferralLink.created_at.desc()))
        ).scalars().all()
    )


async def log_event_clicked(db: AsyncSession, *, ref_code: str) -> ReferralEvent:
    link = (await db.execute(select(ReferralLink).where(ReferralLink.ref_code == ref_code.upper()))).scalar_one_or_none()
    if not link:
        link = (await db.execute(select(ReferralLink).where(ReferralLink.ref_code == ref_code))).scalar_one_or_none()
    if not link:
        raise NotFoundException("Referral link")
    prog = await get_program(db, link.program_id)
    if prog.type == "global_saas" and (prog.rules or {}).get("activation_status") == "inactive":
        raise BadRequestException("Global referral program inactive")
    ev = ReferralEvent(
        id=uuid.uuid4(),
        referrer_user_id=link.user_id,
        referral_program_id=link.program_id,
        referred_user_id=None,
        status="clicked",
        reward_amount=Decimal("0"),
        reward_status="pending",
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


async def update_event_status(db: AsyncSession, *, event_id: uuid.UUID, new_status: str) -> ReferralEvent:
    if new_status not in EVENT_STATUSES:
        raise BadRequestException("Invalid status")
    ev = (await db.execute(select(ReferralEvent).where(ReferralEvent.id == event_id))).scalar_one_or_none()
    if not ev:
        raise NotFoundException("Referral event")
    ev.status = new_status
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


async def issue_reward(db: AsyncSession, *, event_id: uuid.UUID) -> tuple[ReferralEvent, ReferralPayout | None]:
    ev = (await db.execute(select(ReferralEvent).where(ReferralEvent.id == event_id))).scalar_one_or_none()
    if not ev:
        raise NotFoundException("Referral event")
    prog = await get_program(db, ev.referral_program_id)
    if prog.status != "approved":
        raise BadRequestException("Program not approved")
    amt = float(prog.reward_amount)
    if ev.reward_amount and float(ev.reward_amount) > 0:
        amt = float(ev.reward_amount)
    ev.reward_amount = Decimal(str(amt))
    ev.status = "reward_issued"
    ev.reward_status = "approved"
    db.add(ev)
    payout = ReferralPayout(
        id=uuid.uuid4(),
        event_id=ev.id,
        referrer_user_id=ev.referrer_user_id,
        amount=Decimal(str(amt)),
        payout_method=prog.reward_delivery_method,
        payout_status="pending",
    )
    db.add(payout)
    await db.commit()
    await db.refresh(ev)
    await db.refresh(payout)
    await _notify_reward(ev, prog, payout)
    return ev, payout


async def _notify_reward(ev: ReferralEvent, prog: ReferralProgram, payout: ReferralPayout) -> None:
    try:
        from app.core.database import AsyncSessionLocal
        from app.modules.notifications.service import create_notification

        async with AsyncSessionLocal() as db:
            tid_ref = await _tenant_for_user(db, ev.referrer_user_id)
            await create_notification(
                db,
                tenant_id=tid_ref,
                user_id=ev.referrer_user_id,
                kind="system",
                title="Referral reward issued",
                body=f"A reward of {payout.amount} was recorded ({prog.reward_delivery_method}).",
                link="/dashboard/referrals",
                extra={"event_id": str(ev.id), "payout_id": str(payout.id)},
            )
            if prog.type == "tradesman" and prog.owner_id:
                tid_trade = None
                if prog.rules and prog.rules.get("tenant_id"):
                    tid_trade = uuid.UUID(str(prog.rules["tenant_id"]))
                if tid_trade is None:
                    tid_trade = await _tenant_for_user(db, prog.owner_id)
                await create_notification(
                    db,
                    tenant_id=tid_trade,
                    user_id=prog.owner_id,
                    kind="system",
                    title="Client referral reward issued",
                    body=f"A referral reward of {payout.amount} was recorded for your program.",
                    link="/dashboard/referrals",
                    extra={"event_id": str(ev.id), "payout_id": str(payout.id)},
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("referral reward notify failed: %s", exc)


async def _tenant_for_user(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    row = (
        await db.execute(
            select(TenantMember.tenant_id)
            .where(TenantMember.user_id == user_id, TenantMember.role == "owner")
            .limit(1)
        )
    ).scalar_one_or_none()
    if row:
        return row
    row2 = (await db.execute(select(TenantMember.tenant_id).where(TenantMember.user_id == user_id).limit(1))).scalar_one_or_none()
    if not row2:
        raise NotFoundException("Tenant for user")
    return row2


async def request_payout(
    db: AsyncSession,
    *,
    referrer_user_id: uuid.UUID,
    amount: float,
    payout_method: str,
    event_id: uuid.UUID,
) -> ReferralPayout:
    ev = (await db.execute(select(ReferralEvent).where(ReferralEvent.id == event_id))).scalar_one_or_none()
    if not ev or ev.referrer_user_id != referrer_user_id:
        raise ForbiddenException("Invalid event")
    payout = ReferralPayout(
        id=uuid.uuid4(),
        event_id=ev.id,
        referrer_user_id=referrer_user_id,
        amount=Decimal(str(amount)),
        payout_method=payout_method,
        payout_status="pending",
    )
    db.add(payout)
    await db.commit()
    await db.refresh(payout)
    return payout


async def get_payout(db: AsyncSession, payout_id: uuid.UUID) -> ReferralPayout:
    row = (await db.execute(select(ReferralPayout).where(ReferralPayout.id == payout_id))).scalar_one_or_none()
    if not row:
        raise NotFoundException("Referral payout")
    return row


async def referrer_dashboard(db: AsyncSession, referrer_id: uuid.UUID) -> dict[str, Any]:
    clicks = await db.execute(
        select(func.count()).select_from(ReferralEvent).where(
            ReferralEvent.referrer_user_id == referrer_id,
            ReferralEvent.status == "clicked",
        )
    )
    signups = await db.execute(
        select(func.count()).select_from(ReferralEvent).where(
            ReferralEvent.referrer_user_id == referrer_id,
            ReferralEvent.status.in_(
                ("signed_up", "job_started", "job_completed", "invoice_paid", "eligible_for_reward", "reward_issued")
            ),
        )
    )
    paid = await db.execute(
        select(func.count()).select_from(ReferralEvent).where(
            ReferralEvent.referrer_user_id == referrer_id,
            ReferralEvent.status.in_(("eligible_for_reward", "reward_issued")),
        )
    )
    earned = await db.execute(
        select(func.coalesce(func.sum(ReferralPayout.amount), 0)).where(
            ReferralPayout.referrer_user_id == referrer_id,
            ReferralPayout.payout_status.in_(("pending", "approved", "paid")),
        )
    )
    evs = (
        await db.execute(
            select(ReferralEvent)
            .where(ReferralEvent.referrer_user_id == referrer_id)
            .order_by(ReferralEvent.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return {
        "clicks": int(clicks.scalar_one()),
        "signups": int(signups.scalar_one()),
        "paid_users": int(paid.scalar_one()),
        "commission_earned": float(earned.scalar_one()),
        "events": [
            {
                "id": str(e.id),
                "status": e.status,
                "reward_status": e.reward_status,
                "reward_amount": float(e.reward_amount),
                "referred_user_id": str(e.referred_user_id) if e.referred_user_id else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in evs
        ],
    }


def _reward_conditions(rules: dict[str, Any]) -> dict[str, bool]:
    raw = (rules or {}).get("reward_conditions") or {}
    out = {
        "reward_after_signup": True,
        "reward_after_job_completed": True,
        "reward_after_invoice_paid": True,
    }
    for k in out:
        if k in raw:
            out[k] = bool(raw[k])
    return out


async def _user_from_booking(db: AsyncSession, booking: Booking) -> User | None:
    if booking.customer_id:
        cust = (await db.execute(select(Customer).where(Customer.id == booking.customer_id))).scalar_one_or_none()
        if cust and cust.email:
            return (
                await db.execute(select(User).where(func.lower(User.email) == cust.email.lower()))
            ).scalar_one_or_none()
    if booking.customer_email:
        return (
            await db.execute(
                select(User).where(func.lower(User.email) == func.lower(booking.customer_email))
            )
        ).scalar_one_or_none()
    return None


async def _try_issue_reward(db: AsyncSession, event_id: uuid.UUID) -> None:
    try:
        await issue_reward(db, event_id=event_id)
    except BadRequestException:
        pass


# ── Hooks (automation) ───────────────────────────────────────────────────────


async def on_user_signup_with_ref(db: AsyncSession, *, new_user_id: uuid.UUID, ref_code: str | None) -> None:
    if not ref_code:
        return
    link = (
        await db.execute(select(ReferralLink).where(ReferralLink.ref_code == ref_code.strip().upper()))
    ).scalar_one_or_none()
    if not link:
        link = (await db.execute(select(ReferralLink).where(ReferralLink.ref_code == ref_code.strip()))).scalar_one_or_none()
    if not link:
        return
    prev = (
        await db.execute(
            select(ReferralEvent)
            .where(
                ReferralEvent.referral_program_id == link.program_id,
                ReferralEvent.referrer_user_id == link.user_id,
                ReferralEvent.status == "clicked",
                ReferralEvent.referred_user_id.is_(None),
            )
            .order_by(ReferralEvent.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    ev: ReferralEvent | None = None
    if prev:
        prev.referred_user_id = new_user_id
        prev.status = "signed_up"
        db.add(prev)
        ev = prev
    else:
        ev = ReferralEvent(
            id=uuid.uuid4(),
            referrer_user_id=link.user_id,
            referral_program_id=link.program_id,
            referred_user_id=new_user_id,
            status="signed_up",
            reward_amount=Decimal("0"),
            reward_status="pending",
        )
        db.add(ev)
    await db.commit()
    if ev:
        prog = await get_program(db, ev.referral_program_id)
        if prog.type == "tradesman":
            cond = _reward_conditions(prog.rules or {})
            if cond["reward_after_signup"] and not cond["reward_after_job_completed"] and not cond["reward_after_invoice_paid"]:
                ev2 = (await db.execute(select(ReferralEvent).where(ReferralEvent.id == ev.id))).scalar_one_or_none()
                if ev2:
                    ev2.status = "eligible_for_reward"
                    db.add(ev2)
                    await db.commit()
                    await _try_issue_reward(db, ev2.id)


async def on_booking_created(db: AsyncSession, *, tenant_id: uuid.UUID, booking: Booking) -> None:
    user = await _user_from_booking(db, booking)
    if not user:
        return
    evs = (
        await db.execute(
            select(ReferralEvent)
            .join(ReferralProgram, ReferralProgram.id == ReferralEvent.referral_program_id)
            .where(
                ReferralProgram.type == "tradesman",
                ReferralEvent.referred_user_id == user.id,
                ReferralEvent.status == "signed_up",
            )
        )
    ).scalars().all()
    for ev in evs:
        prog = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == ev.referral_program_id))).scalar_one_or_none()
        if not prog or not prog.rules or str(prog.rules.get("tenant_id")) != str(tenant_id):
            continue
        ev.status = "job_started"
        db.add(ev)
    await db.commit()


async def on_booking_completed(db: AsyncSession, *, tenant_id: uuid.UUID, booking: Booking) -> None:
    user = await _user_from_booking(db, booking)
    if not user:
        return
    cust = None
    if booking.customer_id:
        cust = (await db.execute(select(Customer).where(Customer.id == booking.customer_id))).scalar_one_or_none()
    evs = (
        await db.execute(
            select(ReferralEvent)
            .join(ReferralProgram, ReferralProgram.id == ReferralEvent.referral_program_id)
            .where(
                ReferralProgram.type == "tradesman",
                ReferralEvent.referred_user_id == user.id,
                ReferralEvent.status == "job_started",
            )
        )
    ).scalars().all()
    completed_ids: list[uuid.UUID] = []
    for ev in evs:
        prog = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == ev.referral_program_id))).scalar_one_or_none()
        if not prog or str(prog.rules.get("tenant_id")) != str(tenant_id):
            continue
        ev.status = "job_completed"
        db.add(ev)
        completed_ids.append(ev.id)
    await db.commit()
    if cust:
        await maybe_retarget_after_job(db, tenant_id=tenant_id, booking=booking, customer=cust)
    for eid in completed_ids:
        ev = (await db.execute(select(ReferralEvent).where(ReferralEvent.id == eid))).scalar_one_or_none()
        if not ev:
            continue
        prog = await get_program(db, ev.referral_program_id)
        cond = _reward_conditions(prog.rules or {})
        if cond["reward_after_job_completed"] and not cond["reward_after_invoice_paid"]:
            ev.status = "eligible_for_reward"
            db.add(ev)
            await db.commit()
            await _try_issue_reward(db, ev.id)


async def maybe_retarget_after_job(
    db: AsyncSession, *, tenant_id: uuid.UUID, booking: Booking, customer: Customer
) -> None:
    progs = (
        await db.execute(
            select(ReferralProgram).where(
                ReferralProgram.type == "tradesman",
                ReferralProgram.status == "approved",
            )
        )
    ).scalars().all()
    for p in progs:
        if str(p.rules.get("tenant_id")) != str(tenant_id):
            continue
        if not p.rules.get("auto_send_referral_invite_after_job_completion"):
            continue
        if p.rules.get("auto_send_only_to_4_5_star_clients"):
            continue
        limit_days = int(p.rules.get("send_frequency_limit") or 0)
        if limit_days > 0:
            last = p.rules.get("last_referral_invite_sent_at")
            if last:
                from datetime import timedelta

                try:
                    last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) - last_dt < timedelta(days=limit_days):
                        continue
                except Exception:
                    pass
        if not customer.email:
            continue
        body = str(p.rules.get("retarget_email_body") or "Thanks for choosing us — refer a friend and earn rewards.")
        from app.modules.messaging.service import send_message
        from app.modules.messaging.schemas import SendMessageRequest

        await send_message(
            db,
            tenant_id,
            SendMessageRequest(
                customer_id=customer.id,
                channel="email",
                to_address=customer.email,
                subject=str(p.rules.get("retarget_email_subject") or "Refer a friend"),
                body=body,
            ),
        )
        rules = dict(p.rules)
        rules["last_referral_invite_sent_at"] = datetime.now(timezone.utc).isoformat()
        p.rules = rules
        db.add(p)
    await db.commit()


async def on_invoice_paid(db: AsyncSession, *, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> None:
    inv = (
        await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not inv or not inv.customer_id:
        return
    cust = (await db.execute(select(Customer).where(Customer.id == inv.customer_id))).scalar_one_or_none()
    if not cust or not cust.email:
        return
    user = (await db.execute(select(User).where(func.lower(User.email) == cust.email.lower()))).scalar_one_or_none()
    if not user:
        return
    evs = (
        await db.execute(
            select(ReferralEvent)
            .join(ReferralProgram, ReferralProgram.id == ReferralEvent.referral_program_id)
            .where(
                ReferralProgram.type == "tradesman",
                ReferralEvent.referred_user_id == user.id,
                ReferralEvent.status == "job_completed",
            )
        )
    ).scalars().all()
    touched: list[uuid.UUID] = []
    for ev in evs:
        prog = (await db.execute(select(ReferralProgram).where(ReferralProgram.id == ev.referral_program_id))).scalar_one_or_none()
        if not prog or str(prog.rules.get("tenant_id")) != str(tenant_id):
            continue
        cond = _reward_conditions(prog.rules or {})
        if not cond["reward_after_invoice_paid"]:
            continue
        base_pence = inv.total_pence
        if prog.reward_type == "percentage":
            pct = Decimal(str(prog.reward_amount))
            amt = (Decimal(base_pence) * pct / Decimal(100)) / Decimal(100)
            ev.reward_amount = amt.quantize(Decimal("0.01"))
        elif prog.reward_type == "fixed_amount":
            ev.reward_amount = Decimal(str(prog.reward_amount))
        else:
            ev.reward_amount = Decimal(str(prog.reward_amount or 0))
        ev.status = "eligible_for_reward"
        db.add(ev)
        touched.append(ev.id)
    await db.commit()
    for eid in touched:
        await _try_issue_reward(db, eid)


async def advance_reward_if_conditions_met(db: AsyncSession, *, event_id: uuid.UUID) -> None:
    await _try_issue_reward(db, event_id)


async def on_subscription_active_for_tenant(db: AsyncSession, *, tenant_id: uuid.UUID, stripe_status: str) -> None:
    if stripe_status not in ("active", "trialing"):
        return
    owner = (
        await db.execute(
            select(TenantMember.user_id).where(TenantMember.tenant_id == tenant_id, TenantMember.role == "owner").limit(1)
        )
    ).scalar_one_or_none()
    if not owner:
        return
    row = (
        await db.execute(
            select(Subscription, SubscriptionPlan)
            .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
            .where(Subscription.tenant_id == tenant_id)
            .limit(1)
        )
    ).first()
    plan_price_pence = int(row[1].price_gbp_monthly * 100) if row else 0
    evs = (
        await db.execute(
            select(ReferralEvent)
            .join(ReferralProgram, ReferralProgram.id == ReferralEvent.referral_program_id)
            .where(
                ReferralProgram.type == "global_saas",
                ReferralEvent.referred_user_id == owner,
                ReferralEvent.status == "signed_up",
            )
        )
    ).scalars().all()
    ev_ids: list[uuid.UUID] = []
    for ev in evs:
        prog = await get_program(db, ev.referral_program_id)
        if prog.status != "approved" or (prog.rules or {}).get("activation_status") == "inactive":
            continue
        if prog.reward_type == "percentage":
            pct = Decimal(str(prog.reward_amount))
            ev.reward_amount = ((Decimal(plan_price_pence) * pct / Decimal(100)) / Decimal(100)).quantize(Decimal("0.01"))
        else:
            ev.reward_amount = Decimal(str(prog.reward_amount))
        ev.status = "eligible_for_reward"
        ev.reward_status = "pending"
        db.add(ev)
        ev_ids.append(ev.id)
    await db.commit()
    for eid in ev_ids:
        await _try_issue_reward(db, eid)
