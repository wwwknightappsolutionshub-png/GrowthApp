import logging
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def trigger_automation_for_event(ctx: dict, *, tenant_id: str, event: str, entity_id: str, entity_type: str = "deal"):
    """Find active automations for this event and start runs."""
    logger.info("Automation event: tenant=%s event=%s entity=%s type=%s", tenant_id, event, entity_id, entity_type)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.automation.models import Automation, AutomationRun
        from app.modules.automation import service as automation_service
        import uuid

        result = await db.execute(
            select(Automation).where(
                Automation.tenant_id == uuid.UUID(tenant_id),
                Automation.trigger_event == event,
                Automation.is_active == True,
            )
        )
        automations = result.scalars().all()

        for automation in automations:
            entity_uuid = uuid.UUID(entity_id)
            if await automation_service.run_exists_for_entity(db, automation.id, entity_uuid):
                logger.info("Skipping duplicate automation run automation=%s entity=%s", automation.id, entity_id)
                continue

            run = AutomationRun(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                automation_id=automation.id,
                entity_type=entity_type,
                entity_id=entity_uuid,
                status="running",
            )
            db.add(run)
            await db.flush()

            from app.workers.queue import enqueue
            await enqueue("run_automation_step", run_id=str(run.id), step_index=0)

        await db.commit()


async def run_automation_step(ctx: dict, *, run_id: str, step_index: int):
    """Execute a single automation step."""
    logger.info("Running automation step: run=%s step=%s", run_id, step_index)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.automation.models import AutomationRun, AutomationStep
        from app.modules.automation.execution import execute_send_step
        import uuid

        run_result = await db.execute(
            select(AutomationRun).where(AutomationRun.id == uuid.UUID(run_id))
        )
        run = run_result.scalar_one_or_none()
        if not run or run.status not in ("running",):
            return

        step_result = await db.execute(
            select(AutomationStep).where(
                AutomationStep.automation_id == run.automation_id,
                AutomationStep.step_order == step_index,
            )
        )
        step = step_result.scalar_one_or_none()

        if not step:
            run.status = "completed"
            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            return

        config = step.config or {}
        action = step.action_type

        try:
            if action in ("send_sms", "send_email"):
                await execute_send_step(
                    db,
                    tenant_id=run.tenant_id,
                    entity_type=run.entity_type,
                    entity_id=run.entity_id,
                    action=action,
                    config=config,
                )
            elif action == "wait":
                pass
            else:
                logger.warning("Unsupported automation action=%s — skipping", action)
        except Exception as exc:
            logger.error("Automation step failed run=%s step=%s error=%s", run_id, step_index, exc, exc_info=True)
            run.status = "failed"
            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            return

        next_step_result = await db.execute(
            select(AutomationStep).where(
                AutomationStep.automation_id == run.automation_id,
                AutomationStep.step_order == step_index + 1,
            )
        )
        next_step = next_step_result.scalar_one_or_none()

        if next_step:
            from app.workers.queue import enqueue
            delay = next_step.delay_minutes * 60
            await enqueue("run_automation_step", _defer_by=delay, run_id=run_id, step_index=step_index + 1)
        else:
            run.status = "completed"
            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)

        run.current_step = step_index
        db.add(run)
        await db.commit()
