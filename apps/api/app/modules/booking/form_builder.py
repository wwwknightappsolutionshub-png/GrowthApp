"""Booking form templates — category defaults and tenant overrides."""
from __future__ import annotations

import copy
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.tool_config import classifyBusiness_py
from app.modules.booking.enterprise.settings import get_or_create_settings
from app.modules.booking.form_models import BookingFormTemplate
from app.modules.tenants.models import Tenant

BOOKING_CATEGORIES = (
    "tradesman",
    "health_beauty",
    "hospitality",
    "retail",
    "fitness_wellness",
    "professional_services",
    "general",
)

FIELD_TYPES = frozenset(
    {"text", "email", "phone", "textarea", "select", "checkbox", "date", "file", "service", "slot"}
)

SYSTEM_FIELD_IDS = frozenset(
    {
        "customer_name",
        "customer_email",
        "customer_phone",
        "service_id",
        "slot_id",
        "booking_date",
        "start_time",
        "service_description",
    }
)


def default_schema_for_category(category: str) -> dict[str, Any]:
    """Production default booking form per business category."""
    _ = category  # reserved for category-specific presets later
    return {
        "version": 1,
        "fields": [
            {
                "id": "customer_name",
                "type": "text",
                "label": "Your name",
                "required": True,
                "order": 0,
                "system": True,
            },
            {
                "id": "customer_email",
                "type": "email",
                "label": "Email",
                "required": True,
                "order": 1,
                "system": True,
            },
            {
                "id": "customer_phone",
                "type": "phone",
                "label": "Phone",
                "required": False,
                "order": 2,
                "system": True,
            },
            {
                "id": "service_id",
                "type": "service",
                "label": "Service",
                "required": False,
                "order": 3,
                "system": True,
            },
            {
                "id": "slot_id",
                "type": "slot",
                "label": "Available time",
                "required": False,
                "order": 4,
                "system": True,
            },
            {
                "id": "booking_date",
                "type": "date",
                "label": "Preferred date",
                "required": False,
                "order": 5,
                "system": True,
                "hidden_when": "slot_id",
            },
            {
                "id": "start_time",
                "type": "text",
                "label": "Preferred time",
                "required": False,
                "order": 6,
                "system": True,
                "hidden_when": "slot_id",
            },
            {
                "id": "service_description",
                "type": "textarea",
                "label": "What do you need?",
                "required": False,
                "order": 7,
                "system": True,
            },
        ],
    }


def _validate_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, dict):
        raise ValueError("Schema must be an object")
    fields = schema.get("fields")
    if not isinstance(fields, list):
        raise ValueError("Schema must include a fields array")
    seen: set[str] = set()
    for f in fields:
        if not isinstance(f, dict):
            raise ValueError("Each field must be an object")
        fid = str(f.get("id") or "").strip()
        if not fid or fid in seen:
            raise ValueError("Each field needs a unique id")
        seen.add(fid)
        ftype = str(f.get("type") or "text")
        if ftype not in FIELD_TYPES:
            raise ValueError(f"Unsupported field type: {ftype}")
        if "label" not in f:
            raise ValueError(f"Field {fid} requires a label")
    return {"version": int(schema.get("version") or 1), "fields": fields}


def merge_form_schemas(base: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    """Tenant override replaces fields by id and may append new fields."""
    if not override or not override.get("fields"):
        return copy.deepcopy(base)
    base_fields = {f["id"]: copy.deepcopy(f) for f in base.get("fields", []) if f.get("id")}
    for f in override.get("fields", []):
        fid = f.get("id")
        if fid:
            base_fields[fid] = copy.deepcopy(f)
    merged = sorted(base_fields.values(), key=lambda x: int(x.get("order", 0)))
    return {"version": int(override.get("version") or base.get("version") or 1), "fields": merged}


async def get_template(db: AsyncSession, category: str) -> BookingFormTemplate | None:
    return (
        await db.execute(
            select(BookingFormTemplate).where(BookingFormTemplate.category == category)
        )
    ).scalar_one_or_none()


def ensure_booking_form_schema(schema: dict[str, Any] | None, category: str) -> dict[str, Any]:
    """Never return an empty fields list — public booking must always be usable."""
    default = default_schema_for_category(category)
    if not schema or not isinstance(schema.get("fields"), list) or len(schema["fields"]) == 0:
        return copy.deepcopy(default)
    return schema


async def get_or_seed_template(db: AsyncSession, category: str) -> dict[str, Any]:
    row = await get_template(db, category)
    default = default_schema_for_category(category)
    if not row:
        row = BookingFormTemplate(
            category=category,
            name=f"{category.replace('_', ' ').title()} booking form",
            schema=default,
        )
        db.add(row)
        await db.commit()
        return default
    ensured = ensure_booking_form_schema(row.schema, category)
    if not (row.schema or {}).get("fields"):
        row.schema = ensured
        await db.commit()
    return ensured


async def resolve_tenant_booking_form(
    db: AsyncSession, tenant: Tenant
) -> dict[str, Any]:
    category = classifyBusiness_py(tenant.business_type or "general")
    base = await get_or_seed_template(db, category)
    settings = await get_or_create_settings(db, tenant.id)
    override = getattr(settings, "booking_form_override", None) or {}
    merged = merge_form_schemas(base, override if isinstance(override, dict) else None)
    return ensure_booking_form_schema(merged, category)


async def normalize_public_booking_payload(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Coerce widget submissions into PublicBookingCreate-compatible fields."""
    from datetime import date as date_type

    from app.modules.booking.models import AvailabilitySlot

    out: dict[str, Any] = {}
    for key, value in body.items():
        if value is None or value == "":
            continue
        out[key] = value

    slot_raw = out.get("slot_id")
    if slot_raw:
        try:
            slot_uuid = uuid.UUID(str(slot_raw))
        except ValueError:
            out.pop("slot_id", None)
        else:
            slot = (
                await db.execute(
                    select(AvailabilitySlot).where(
                        AvailabilitySlot.id == slot_uuid,
                        AvailabilitySlot.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            if not slot:
                raise ValueError("Selected time slot is no longer available")
            if slot.is_booked:
                raise ValueError("This slot is already booked")
            out["booking_date"] = slot.slot_date.isoformat()
            out["start_time"] = slot.start_time.strftime("%H:%M:%S")
            out["slot_id"] = str(slot.id)
            if slot.staff_id and not out.get("staff_id"):
                out["staff_id"] = str(slot.staff_id)
            if slot.service_id and not out.get("service_id"):
                out["service_id"] = str(slot.service_id)

    for key in ("service_id", "staff_id", "location_id", "resource_id"):
        if key not in out:
            continue
        try:
            out[key] = str(uuid.UUID(str(out[key])))
        except ValueError:
            out.pop(key, None)

    st = out.get("start_time")
    if isinstance(st, str) and len(st) == 5 and ":" in st:
        out["start_time"] = f"{st}:00"

    bd = out.get("booking_date")
    if isinstance(bd, str) and bd:
        try:
            date_type.fromisoformat(bd[:10])
        except ValueError as exc:
            raise ValueError("Invalid booking date") from exc

    if not out.get("customer_name", "").strip():
        raise ValueError("Your name is required")
    if not out.get("booking_date") or not out.get("start_time"):
        raise ValueError("Please select an available time or enter a preferred date and time")

    return out


def map_submission_to_booking(
    payload: dict[str, Any], schema: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split system booking fields vs custom/intake responses."""
    system_ids = {f["id"] for f in schema.get("fields", []) if f.get("system")}
    system_ids |= SYSTEM_FIELD_IDS
    booking: dict[str, Any] = {}
    intake: dict[str, Any] = {}
    custom: dict[str, Any] = {}
    for key, value in payload.items():
        if key in system_ids:
            booking[key] = value
        elif key.startswith("custom_"):
            custom[key] = value
        else:
            intake[key] = value
    return booking, {"intake_responses": intake, "custom_fields": custom}


async def list_all_templates(db: AsyncSession) -> list[BookingFormTemplate]:
    rows = (await db.execute(select(BookingFormTemplate).order_by(BookingFormTemplate.category))).scalars().all()
    if len(rows) < len(BOOKING_CATEGORIES):
        for cat in BOOKING_CATEGORIES:
            await get_or_seed_template(db, cat)
        rows = (await db.execute(select(BookingFormTemplate).order_by(BookingFormTemplate.category))).scalars().all()
    return list(rows)


async def upsert_template(
    db: AsyncSession,
    category: str,
    schema: dict[str, Any],
    *,
    name: str | None = None,
    user_id: uuid.UUID | None = None,
) -> BookingFormTemplate:
    if category not in BOOKING_CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    validated = _validate_schema(schema)
    row = await get_template(db, category)
    if row:
        row.schema = validated
        if name:
            row.name = name
        row.updated_by = user_id
    else:
        row = BookingFormTemplate(
            category=category,
            name=name or f"{category} booking form",
            schema=validated,
            updated_by=user_id,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_tenant_form_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    override: dict[str, Any],
    *,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    from app.modules.booking.enterprise.settings import update_settings
    from app.modules.booking.enterprise_schemas import BookingSettingsUpdate

    validated = _validate_schema(override) if override.get("fields") else {"version": 1, "fields": []}
    await update_settings(
        db,
        tenant_id,
        BookingSettingsUpdate(booking_form_override=validated),
        user_id=user_id,
    )
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    return await resolve_tenant_booking_form(db, tenant)
