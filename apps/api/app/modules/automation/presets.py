"""Recommended automation presets — templates + workflow definitions."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.automation.models import Automation, AutomationStep, MessageTemplate
from app.modules.automation.schemas import AutomationCreate, AutomationStepIn

PRESET_KEYS = ("lead_welcome", "quote_followup", "job_review")

PRESET_META: dict[str, dict[str, str]] = {
    "lead_welcome": {
        "name": "New lead welcome sequence",
        "description": "Instant SMS acknowledgement plus a follow-up email the next day.",
        "trigger_event": "lead_created",
    },
    "quote_followup": {
        "name": "Quote follow-up nudge",
        "description": "Email after 48 hours, then SMS if still no response.",
        "trigger_event": "quote_sent",
    },
    "job_review": {
        "name": "Job completed → review request",
        "description": "SMS review link 2 hours after completion, email reminder after 7 days.",
        "trigger_event": "job_completed",
    },
}


def _template_defs(preset_key: str) -> list[dict[str, Any]]:
    if preset_key == "lead_welcome":
        return [
            {
                "name": "Lead welcome SMS",
                "channel": "sms",
                "subject": None,
                "body": (
                    "Hi {{first_name}}, thanks for contacting {{business_name}}. "
                    "We received your enquiry and will be in touch shortly."
                ),
            },
            {
                "name": "Lead welcome email",
                "channel": "email",
                "subject": "Thanks for getting in touch — {{business_name}}",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "Thank you for reaching out to {{business_name}}. "
                    "We will review your enquiry and respond as soon as we can.\n\n"
                    "You can also book online: {{booking_url}}\n\n"
                    "Best regards,\n{{business_name}}"
                ),
            },
        ]
    if preset_key == "quote_followup":
        return [
            {
                "name": "Quote follow-up email",
                "channel": "email",
                "subject": "Your quote {{quote_number}} from {{business_name}}",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "Just checking in on quote {{quote_number}}. "
                    "You can view and accept it here: {{quote_url}}\n\n"
                    "Reply to this email if you have any questions.\n\n"
                    "{{business_name}}"
                ),
            },
            {
                "name": "Quote follow-up SMS",
                "channel": "sms",
                "subject": None,
                "body": (
                    "Hi {{first_name}}, any questions on your quote from {{business_name}}? "
                    "View it here: {{quote_url}}"
                ),
            },
        ]
    if preset_key == "job_review":
        return [
            {
                "name": "Review request SMS",
                "channel": "sms",
                "subject": None,
                "body": (
                    "Hi {{first_name}}, thank you for choosing {{business_name}}! "
                    "Could you spare 30 seconds to rate your experience? {{review_url}}"
                ),
            },
            {
                "name": "Review reminder email",
                "channel": "email",
                "subject": "How did we do? — {{business_name}}",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "We hope you were happy with your recent {{service_type}} service. "
                    "Your feedback helps us improve — please leave a quick review:\n\n"
                    "{{review_url}}\n\n"
                    "Thank you,\n{{business_name}}"
                ),
            },
        ]
    raise ValueError(f"Unknown preset: {preset_key}")


def _steps_for_preset(preset_key: str, template_ids: list[str]) -> list[AutomationStepIn]:
    if preset_key == "lead_welcome":
        return [
            AutomationStepIn(step_order=0, action_type="send_sms", delay_minutes=0, config={"template_id": template_ids[0]}),
            AutomationStepIn(step_order=1, action_type="wait", delay_minutes=0, config={}),
            AutomationStepIn(step_order=2, action_type="send_email", delay_minutes=1440, config={"template_id": template_ids[1]}),
        ]
    if preset_key == "quote_followup":
        return [
            AutomationStepIn(step_order=0, action_type="wait", delay_minutes=0, config={}),
            AutomationStepIn(step_order=1, action_type="send_email", delay_minutes=2880, config={"template_id": template_ids[0]}),
            AutomationStepIn(step_order=2, action_type="wait", delay_minutes=0, config={}),
            AutomationStepIn(step_order=3, action_type="send_sms", delay_minutes=4320, config={"template_id": template_ids[1]}),
        ]
    if preset_key == "job_review":
        return [
            AutomationStepIn(step_order=0, action_type="wait", delay_minutes=0, config={}),
            AutomationStepIn(
                step_order=1,
                action_type="send_sms",
                delay_minutes=120,
                config={"template_id": template_ids[0], "create_review_request": True},
            ),
            AutomationStepIn(step_order=2, action_type="wait", delay_minutes=0, config={}),
            AutomationStepIn(step_order=3, action_type="send_email", delay_minutes=10080, config={"template_id": template_ids[1]}),
        ]
    raise ValueError(f"Unknown preset: {preset_key}")


async def list_available_presets(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
    installed: set[str] = set()
    result = await db.execute(
        select(Automation).where(Automation.tenant_id == tenant_id, Automation.is_active == True)
    )
    for automation in result.scalars().all():
        for key, meta in PRESET_META.items():
            if automation.name == meta["name"]:
                installed.add(key)

    return [
        {
            "key": key,
            **PRESET_META[key],
            "installed": key in installed,
        }
        for key in PRESET_KEYS
    ]


async def install_preset(db: AsyncSession, tenant_id: uuid.UUID, preset_key: str) -> Automation:
    if preset_key not in PRESET_KEYS:
        raise ValueError(f"Unknown preset: {preset_key}")

    meta = PRESET_META[preset_key]
    existing = await db.execute(
        select(Automation).where(Automation.tenant_id == tenant_id, Automation.name == meta["name"])
    )
    if existing.scalar_one_or_none():
        raise ValueError("Preset already installed")

    template_ids: list[str] = []
    for tpl in _template_defs(preset_key):
        created = MessageTemplate(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=tpl["name"],
            channel=tpl["channel"],
            subject=tpl.get("subject"),
            body=tpl["body"],
        )
        db.add(created)
        await db.flush()
        template_ids.append(str(created.id))

    from app.modules.automation import service

    data = AutomationCreate(
        name=meta["name"],
        trigger_event=meta["trigger_event"],
        is_active=True,
        steps=_steps_for_preset(preset_key, template_ids),
    )
    return await service.create_automation(db, tenant_id, data)


async def install_all_presets(db: AsyncSession, tenant_id: uuid.UUID) -> list[Automation]:
    installed: list[Automation] = []
    for key in PRESET_KEYS:
        try:
            installed.append(await install_preset(db, tenant_id, key))
        except ValueError as exc:
            if "already installed" not in str(exc):
                raise
    return installed
