"""
GDPR endpoints — owner-only.

POST /gdpr/export  → create export request + enqueue gdpr_export
POST /gdpr/erasure → create erasure request for a specific customer + enqueue gdpr_erase
GET  /gdpr/requests → list all GDPR requests for the tenant
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import OwnerContext
from app.core.exceptions import NotFoundException
from app.modules.auth.schemas import MessageResponse
from app.modules.crm.models import Customer
from app.modules.gdpr.models import GdprRequest
from app.workers.queue import enqueue

router = APIRouter(prefix="/gdpr", tags=["GDPR"])


class GDPRRequestOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    customer_id: uuid.UUID | None = None
    download_url: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ErasureBody(BaseModel):
    customer_id: uuid.UUID


@router.post("/export", response_model=MessageResponse, status_code=202)
async def request_export(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    """Request a GDPR data export. Owner-only. Enqueues a background job."""
    _, tenant, _ = ctx
    req = GdprRequest(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        type="export",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(req)
    await db.commit()
    await enqueue("gdpr_export", gdpr_request_id=str(req.id))
    return MessageResponse(message="Export queued. You will receive an email when it is ready.")


@router.post("/erasure", response_model=MessageResponse, status_code=202)
async def request_erasure(
    body: ErasureBody,
    ctx: OwnerContext,
    db: AsyncSession = Depends(get_db),
):
    """Request right-to-erasure for a specific customer. Owner-only."""
    _, tenant, _ = ctx

    # Verify the customer belongs to this tenant before queuing.
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == body.customer_id,
                Customer.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer")

    req = GdprRequest(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        customer_id=body.customer_id,
        type="erasure",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(req)
    await db.commit()
    await enqueue("gdpr_erase", gdpr_request_id=str(req.id))
    return MessageResponse(message="Erasure queued. Personally-identifiable data will be redacted shortly.")


@router.get("/requests", response_model=list[GDPRRequestOut])
async def list_requests(ctx: OwnerContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    rows = (
        await db.execute(
            select(GdprRequest)
            .where(GdprRequest.tenant_id == tenant.id)
            .order_by(GdprRequest.created_at.desc())
        )
    ).scalars().all()
    return [GDPRRequestOut.model_validate(r) for r in rows]
