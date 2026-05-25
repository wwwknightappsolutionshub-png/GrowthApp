import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.modules.automation.models import Automation, AutomationRun, AutomationStep, MessageTemplate
from app.modules.automation.schemas import AutomationCreate, AutomationUpdate, MessageTemplateCreate


async def list_automations(db: AsyncSession, tenant_id: uuid.UUID) -> list[Automation]:
    result = await db.execute(select(Automation).options(selectinload(Automation.steps)).where(Automation.tenant_id == tenant_id))
    return list(result.scalars().all())


async def tenant_has_active_automation(db: AsyncSession, tenant_id: uuid.UUID, trigger_event: str) -> bool:
    result = await db.execute(
        select(func.count())
        .select_from(Automation)
        .where(
            Automation.tenant_id == tenant_id,
            Automation.trigger_event == trigger_event,
            Automation.is_active == True,
        )
    )
    return (result.scalar() or 0) > 0


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
    steps_data = data.steps
    payload = data.model_dump(exclude_none=True, exclude={"steps"})
    for field, value in payload.items():
        setattr(a, field, value)
    if steps_data is not None:
        for old in list(a.steps):
            await db.delete(old)
        await db.flush()
        for step_data in steps_data:
            step = AutomationStep(id=uuid.uuid4(), automation_id=a.id, **step_data.model_dump())
            db.add(step)
    db.add(a)
    await db.commit()
    return await get_automation(db, tenant_id, automation_id)


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


async def run_exists_for_entity(
    db: AsyncSession,
    automation_id: uuid.UUID,
    entity_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        select(func.count())
        .select_from(AutomationRun)
        .where(
            AutomationRun.automation_id == automation_id,
            AutomationRun.entity_id == entity_id,
        )
    )
    return (result.scalar() or 0) > 0
