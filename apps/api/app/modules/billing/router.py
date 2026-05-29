from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext, OwnerContext
from app.core.exceptions import NotFoundException
from app.modules.billing.models import BillingInvoice, Subscription, SubscriptionPlan
from app.modules.billing.schemas import (
    BillingInvoiceResponse, CheckoutRequest, CheckoutResponse,
    PlanResponse, PortalResponse, SubscriptionResponse,
)

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan))
    return list(result.scalars().all())


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.tenant_id == tenant.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise NotFoundException("Subscription")
    return sub


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    from app.adapters import get_payment_adapter
    _, tenant, _ = ctx
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == data.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan or not plan.stripe_price_id:
        raise NotFoundException("Plan")

    adapter = get_payment_adapter()
    customer_id = await adapter.create_customer(
        email=tenant.email or "", name=tenant.name, metadata={"tenant_id": str(tenant.id)}
    )
    session = await adapter.create_checkout_session(
        customer_id=customer_id,
        price_id=plan.stripe_price_id,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )
    return CheckoutResponse(checkout_url=session.checkout_url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    from app.adapters import get_payment_adapter
    _, tenant, _ = ctx
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == tenant.id)
    )
    sub = result.scalar_one_or_none()
    if not sub or not sub.stripe_customer_id:
        raise NotFoundException("Subscription")

    adapter = get_payment_adapter()
    url = await adapter.create_customer_portal(
        customer_id=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/dashboard/settings/billing",
    )
    return PortalResponse(portal_url=url)


@router.get("/invoices", response_model=list[BillingInvoiceResponse])
async def list_invoices(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    result = await db.execute(
        select(BillingInvoice).where(BillingInvoice.tenant_id == tenant.id).order_by(BillingInvoice.created_at.desc())
    )
    return list(result.scalars().all())
