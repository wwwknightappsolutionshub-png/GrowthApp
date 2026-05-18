"""Super Admin — Helpdesk & Support Tools.

GET    /api/admin/support/tickets
GET    /api/admin/support/tickets/{ticket_id}
POST   /api/admin/support/tickets
PUT    /api/admin/support/tickets/{ticket_id}
DELETE /api/admin/support/tickets/{ticket_id}
POST   /api/admin/support/tickets/{ticket_id}/resolve
POST   /api/admin/support/tickets/{ticket_id}/reply
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin
from app.core.rbac import SupportTicket, TicketReply

router = APIRouter(prefix="/api/admin/support", tags=["Admin — Support"])


class TicketCreate(BaseModel):
    tenant_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    subject: str
    body: str
    priority: str = "normal"


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class ReplyBody(BaseModel):
    body: str
    is_internal: bool = False


@router.get("/tickets")
async def list_tickets(
    _: SuperAdmin,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(SupportTicket).order_by(desc(SupportTicket.created_at))
    if status:
        q = q.where(SupportTicket.status == status)
    if priority:
        q = q.where(SupportTicket.priority == priority)
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()
    return [
        {
            "id": str(r.id), "subject": r.subject, "status": r.status,
            "priority": r.priority, "tenant_id": str(r.tenant_id) if r.tenant_id else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Ticket not found")
    replies = (await db.execute(select(TicketReply).where(TicketReply.ticket_id == ticket_id).order_by(TicketReply.created_at))).scalars().all()
    return {
        "id": str(t.id), "subject": t.subject, "body": t.body, "status": t.status,
        "priority": t.priority, "created_at": t.created_at.isoformat(),
        "replies": [{"id": str(r.id), "body": r.body, "is_internal": r.is_internal, "created_at": r.created_at.isoformat()} for r in replies],
    }


@router.post("/tickets", status_code=201)
async def create_ticket(body: TicketCreate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = SupportTicket(**body.model_dump(), status="open")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "subject": t.subject}


@router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: uuid.UUID, body: TicketUpdate, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Ticket not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    await db.commit()
    return {"id": str(t.id), "status": t.status}


@router.delete("/tickets/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Ticket not found")
    await db.delete(t)
    await db.commit()


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: uuid.UUID, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Ticket not found")
    t.status = "resolved"
    await db.commit()
    return {"id": str(t.id), "status": t.status}


@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(ticket_id: uuid.UUID, body: ReplyBody, admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Ticket not found")
    r = TicketReply(ticket_id=ticket_id, author_id=admin.id, body=body.body, is_internal=body.is_internal)
    db.add(r)
    if t.status == "open":
        t.status = "pending"
    await db.commit()
    await db.refresh(r)
    return {"id": str(r.id), "body": r.body}
