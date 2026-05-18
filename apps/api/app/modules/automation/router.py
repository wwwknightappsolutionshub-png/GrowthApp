from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentTenantContext
from app.modules.automation import service
from app.modules.automation.schemas import (
    AutomationCreate, AutomationUpdate, AutomationResponse,
    MessageTemplateCreate, MessageTemplateResponse,
)
from app.modules.auth.schemas import MessageResponse

router = APIRouter(prefix="/automations", tags=["Automations"])


@router.get("", response_model=list[AutomationResponse])
async def list_automations(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_automations(db, tenant.id)


@router.post("", response_model=AutomationResponse, status_code=201)
async def create_automation(data: AutomationCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.create_automation(db, tenant.id, data)


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(automation_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.get_automation(db, tenant.id, automation_id)


@router.patch("/{automation_id}", response_model=AutomationResponse)
async def update_automation(automation_id: UUID, data: AutomationUpdate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.update_automation(db, tenant.id, automation_id, data)


@router.delete("/{automation_id}", response_model=MessageResponse)
async def delete_automation(automation_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.delete_automation(db, tenant.id, automation_id)
    return MessageResponse(message="Automation deleted")


@router.get("/templates", response_model=list[MessageTemplateResponse])
async def list_templates(ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.list_templates(db, tenant.id)


@router.post("/templates", response_model=MessageTemplateResponse, status_code=201)
async def create_template(data: MessageTemplateCreate, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    return await service.create_template(db, tenant.id, data)


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_template(template_id: UUID, ctx: CurrentTenantContext, db: AsyncSession = Depends(get_db)):
    _, tenant, _ = ctx
    await service.delete_template(db, tenant.id, template_id)
    return MessageResponse(message="Template deleted")
