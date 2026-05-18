import logging
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


async def trigger_automation_for_event(ctx: dict, *, tenant_id: str, event: str, entity_id: str, entity_type: str = "deal"):
    """Find active automations for this event and start runs."""
    logger.info("Automation event: tenant=%s event=%s entity=%s", tenant_id, event, entity_id)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.automation.models import Automation, AutomationRun
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
            run = AutomationRun(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                automation_id=automation.id,
                entity_type=entity_type,
                entity_id=uuid.UUID(entity_id),
                status="running",
            )
            db.add(run)
            await db.flush()

            # Schedule first step
            from app.workers.queue import enqueue
            await enqueue("run_automation_step", run_id=str(run.id), step_index=0)

        await db.commit()


async def run_automation_step(ctx: dict, *, run_id: str, step_index: int):
    """Execute a single automation step."""
    logger.info("Running automation step: run=%s step=%s", run_id, step_index)
    async with get_db_context() as db:
        from sqlalchemy import select
        from app.modules.automation.models import AutomationRun, AutomationStep
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
            # All steps done
            run.status = "completed"
            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            return

        config = step.config or {}
        action = step.action_type

        if action == "send_sms":
            # Get entity phone number
            from app.workers.queue import enqueue
            # Simplified: would normally resolve entity -> customer -> phone
            logger.info("Auto-SMS step: template=%s", config.get("template_id"))

        elif action == "send_email":
            logger.info("Auto-email step: template=%s", config.get("template_id"))

        elif action == "wait":
            pass  # delay_minutes handled by ARQ defer

        # Schedule next step
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
