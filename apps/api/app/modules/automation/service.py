import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.modules.automation.models import Automation, AutomationStep, MessageTemplate
from app.modules.automation.schemas import AutomationCreate, AutomationUpdate, MessageTemplateCreate


async def list_automations(db: AsyncSession, tenant_id: uuid.UUID) -> list[Automation]:
    result = await db.execute(select(Automation).options(selectinload(Automation.steps)).where(Automation.tenant_id == tenant_id))
    return list(result.scalars().all())


async def create_automation(db: AsyncSession, tenant_id: uuid.UUID, data: AutomationCreate) -> Automation:
    automation = Automation(id=uuid.uuid4(), tenant_id=tenant_id, name=data.name, trigger_event=data.trigger_event, trigger_conditions=data.trigger_conditions, is_active=data.is_active)
    db.add(automation)
    await db.flush()
    for step_data in data.steps:
        step = AutomationStep(id=uuid.uuid4(), automation_id=automation.id, **step_data.model_dump())
        db.add(step)
    await db.commit()
    return await get_automation(db, tenant_id, automation.id)


async def get_automation(db: AsyncSession, tenant_id: uuid.UUID, automation_id: uuid.UUID) -> Automation:
    result = await db.execute(select(Automation).options(selectinload(Automation.steps)).where(Automation.id == automation_id, Automation.tenant_id == tenant_id))
    a = result.scalar_one_or_none()
    if not a:
        raise NotFoundException("Automation")
    return a


async def update_automation(db: AsyncSession, tenant_id: uuid.UUID, automation_id: uuid.UUID, data: AutomationUpdate) -> Automation:
    a = await get_automation(db, tenant_id, automation_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(a, field, value)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


async def delete_automation(db: AsyncSession, tenant_id: uuid.UUID, automation_id: uuid.UUID) -> None:
    a = await get_automation(db, tenant_id, automation_id)
    await db.delete(a)
    await db.commit()


async def list_templates(db: AsyncSession, tenant_id: uuid.UUID) -> list[MessageTemplate]:
    result = await db.execute(select(MessageTemplate).where(MessageTemplate.tenant_id == tenant_id))
    return list(result.scalars().all())


async def create_template(db: AsyncSession, tenant_id: uuid.UUID, data: MessageTemplateCreate) -> MessageTemplate:
    t = MessageTemplate(id=uuid.uuid4(), tenant_id=tenant_id, **data.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


async def delete_template(db: AsyncSession, tenant_id: uuid.UUID, template_id: uuid.UUID) -> None:
    result = await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id, MessageTemplate.tenant_id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundException("Template")
    await db.delete(t)
    await db.commit()
