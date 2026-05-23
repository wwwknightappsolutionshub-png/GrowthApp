"""
Seed a demo garage tenant with all industry add-ons and sample data.

Used by scripts/seed_garage_addons.py and scripts/seed_data.py.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.addons.common.constants import (
    FEATURE_INDUSTRY_BILLING,
    FEATURE_INDUSTRY_BOOKING,
    FEATURE_INDUSTRY_CRM,
    Vertical,
)
from app.modules.addons.common.models import TenantIndustryProfile
from app.modules.addons.common.service import grant_addon
from app.modules.addons.industry_models import (
    BookingPartsReservation,
    BookingProductCatalog,
    BookingResourceAllocation,
    BookingSessionService,
    CustomerGarageScore,
    IndustryInvoiceTemplate,
    IndustryServicePackage,
    InvoiceTip,
    InvoiceWarranty,
    MaintenancePrediction,
    MechanicSkill,
    PartsInventory,
    PartsMarkupRule,
    Vehicle,
    VehiclePartsUsage,
    VehicleServiceRecord,
    VehicleServiceEstimate,
)
from app.modules.auth.models import User
from app.modules.booking.enterprise_models import BookingResource, BookingService
from app.modules.booking.models import Booking, Staff
from app.modules.billing.models import Subscription, SubscriptionPlan
from app.modules.crm.models import Customer
from app.modules.quotes_invoices.models import Invoice, InvoiceItem
from app.modules.tenants.models import Location, Tenant, TenantMember

# Default demo credentials (printed after seed)
GARAGE_DEMO_EMAIL = "garage@knightmotors.co.uk"
GARAGE_DEMO_PASSWORD = "Garage@Test1"
GARAGE_DEMO_SLUG = "knight-motors-garage"
GARAGE_DEMO_NAME = "Knight Motors Garage"

DEFAULT_GARAGE_SETTINGS = {
    "vertical": "garage",
    "auto_parts_check_on_booking": True,
    "default_bay_count": 4,
    "parts_markup_default_percent": 25,
    "vin_lookup_enabled": True,
    "maintenance_predictions_enabled": True,
    "industry_addons_enabled": True,
}


async def ensure_garage_demo_tenant(
    db: AsyncSession,
    *,
    plans: dict[str, SubscriptionPlan] | None = None,
) -> dict:
    """Create or update garage demo user, tenant, addons, and sample data."""
    now = datetime.now(timezone.utc)
    email = GARAGE_DEMO_EMAIL.lower()

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(GARAGE_DEMO_PASSWORD),
            full_name="Alex Knight",
            email_verified_at=now,
            onboarding_completed=True,
            totp_backup_codes=[],
        )
        db.add(user)
        await db.flush()

    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == GARAGE_DEMO_SLUG))
    ).scalar_one_or_none()
    if not tenant:
        plan = None
        if plans:
            plan = plans.get("Growth") or plans.get("Pro") or next(iter(plans.values()), None)
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=GARAGE_DEMO_SLUG,
            name=GARAGE_DEMO_NAME,
            business_type="garage",
            phone="0113 496 0001",
            email=email,
            city="Leeds",
            postcode="LS1 4DY",
            plan_id=plan.id if plan else None,
            trial_ends_at=now + timedelta(days=30),
            is_active=True,
            onboarding_completed=True,
        )
        db.add(tenant)
        await db.flush()

        loc = Location(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            slug=f"{GARAGE_DEMO_SLUG}-main",
            name=f"{GARAGE_DEMO_NAME} — Workshop",
            address="42 Industrial Way",
            city="Leeds",
            postcode="LS1 4DY",
            phone="0113 496 0001",
            email=email,
            is_primary=True,
        )
        db.add(loc)

        if plan:
            db.add(
                Subscription(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    status="active",
                    current_period_start=now,
                    current_period_end=now + timedelta(days=30),
                )
            )

    member = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant.id, TenantMember.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if not member:
        db.add(
            TenantMember(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                user_id=user.id,
                role="owner",
                joined_at=now,
            )
        )

    profile = (
        await db.execute(
            select(TenantIndustryProfile).where(TenantIndustryProfile.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()
    if profile:
        profile.vertical = Vertical.GARAGE.value
        profile.settings = {**DEFAULT_GARAGE_SETTINGS, **(profile.settings or {})}
    else:
        db.add(
            TenantIndustryProfile(
                tenant_id=tenant.id,
                vertical=Vertical.GARAGE.value,
                settings=DEFAULT_GARAGE_SETTINGS,
            )
        )

    for code in (FEATURE_INDUSTRY_BOOKING, FEATURE_INDUSTRY_BILLING, FEATURE_INDUSTRY_CRM):
        await grant_addon(db, tenant.id, code)

    counts = await _seed_garage_sample_data(db, tenant)
    await db.commit()

    return {
        "email": email,
        "password": GARAGE_DEMO_PASSWORD,
        "tenant_id": str(tenant.id),
        "tenant_slug": tenant.slug,
        "user_id": str(user.id),
        **counts,
    }


async def _seed_garage_sample_data(db: AsyncSession, tenant: Tenant) -> dict:
    tid = tenant.id
    today = date.today()

    # Services
    services = []
    for name, mins, price in [
        ("Full MOT", 60, 5495),
        ("Interim service", 90, 12900),
        ("Brake pad replacement", 120, 18900),
        ("Diagnostics", 45, 7500),
    ]:
        existing = (
            await db.execute(
                select(BookingService).where(
                    BookingService.tenant_id == tid, BookingService.name == name
                )
            )
        ).scalar_one_or_none()
        if existing:
            services.append(existing)
        else:
            s = BookingService(
                tenant_id=tid,
                name=name,
                duration_minutes=mins,
                price_pence=price,
                is_active=True,
            )
            db.add(s)
            services.append(s)
    await db.flush()

    # Bays
    bays = []
    for i in range(1, 5):
        name = f"Bay {i}"
        bay = (
            await db.execute(
                select(BookingResource).where(
                    BookingResource.tenant_id == tid, BookingResource.name == name
                )
            )
        ).scalar_one_or_none()
        if not bay:
            bay = BookingResource(
                tenant_id=tid,
                name=name,
                resource_type="bay",
                capacity=1,
                is_active=True,
            )
            db.add(bay)
        bays.append(bay)
    await db.flush()

    # Mechanic staff
    mechanics = []
    for name, email, spec in [
        ("Jamie Owen", "jamie@knightmotors.co.uk", "mot"),
        ("Chris Bell", "chris@knightmotors.co.uk", "diagnostics"),
    ]:
        st = (
            await db.execute(
                select(Staff).where(Staff.tenant_id == tid, Staff.email == email)
            )
        ).scalar_one_or_none()
        if not st:
            st = Staff(tenant_id=tid, name=name, email=email, role="staff", is_active=True)
            db.add(st)
        mechanics.append((st, spec))
    await db.flush()

    for st, spec in mechanics:
        exists = (
            await db.execute(
                select(MechanicSkill).where(
                    MechanicSkill.tenant_id == tid,
                    MechanicSkill.staff_id == st.id,
                    MechanicSkill.skill_code == spec,
                )
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(
                MechanicSkill(
                    tenant_id=tid,
                    staff_id=st.id,
                    skill_code=spec,
                    certification_level="senior",
                )
            )

    # Parts
    parts = []
    for sku, name, qty, cost in [
        ("OIL-5W30", "Engine oil 5W30", 24, 850),
        ("FILTER-OIL", "Oil filter", 18, 1200),
        ("PAD-FRONT", "Front brake pads", 8, 4500),
        ("PLUG-IRIDIUM", "Spark plugs (set)", 12, 3200),
    ]:
        p = (
            await db.execute(
                select(PartsInventory).where(PartsInventory.tenant_id == tid, PartsInventory.sku == sku)
            )
        ).scalar_one_or_none()
        if not p:
            p = PartsInventory(
                tenant_id=tid,
                sku=sku,
                name=name,
                category="consumables" if "OIL" in sku or "FILTER" in sku else "brakes",
                qty_on_hand=qty,
                unit_cost_pence=cost,
                reorder_level=5,
            )
            db.add(p)
        parts.append(p)
    await db.flush()

    # Markup rules
    for cat, pct in [("consumables", 20), ("brakes", 35), ("general", 25)]:
        exists = (
            await db.execute(
                select(PartsMarkupRule).where(
                    PartsMarkupRule.tenant_id == tid, PartsMarkupRule.category == cat
                )
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(PartsMarkupRule(tenant_id=tid, category=cat, markup_percent=pct))

    # Duration estimates
    for make, model, svc, mins in [
        ("Ford", "Focus", "mot", 55),
        ("VW", "Golf", "mot", 60),
        ("BMW", "320d", "Interim service", 95),
    ]:
        exists = (
            await db.execute(
                select(VehicleServiceEstimate).where(
                    VehicleServiceEstimate.tenant_id == tid,
                    VehicleServiceEstimate.make == make,
                    VehicleServiceEstimate.model == model,
                    VehicleServiceEstimate.service_name == svc,
                )
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(
                VehicleServiceEstimate(
                    tenant_id=tid,
                    make=make,
                    model=model,
                    service_name=svc,
                    estimated_minutes=mins,
                )
            )

    # Customers + vehicles
    customers = []
    vehicles = []
    for fn, ln, em, vin, make, model, reg in [
        ("Tom", "Harper", "tom.harper@example.com", "WVWZZZ3CZWE123456", "VW", "Golf", "KN18 MOT"),
        ("Lisa", "Grant", "lisa.grant@example.com", "WF0EXXGBBE8A12345", "Ford", "Focus", "LS19 GRT"),
        ("Mark", "Steele", "mark.steele@example.com", "SBM13A1B50E123789", "BMW", "320d", "YK12 STL"),
    ]:
        c = (
            await db.execute(
                select(Customer).where(Customer.tenant_id == tid, Customer.email == em)
            )
        ).scalar_one_or_none()
        if not c:
            c = Customer(
                tenant_id=tid,
                first_name=fn,
                last_name=ln,
                email=em,
                phone="07700 900 001",
                postcode="LS2 8BE",
                gdpr_consent=True,
                gdpr_consent_at=datetime.now(timezone.utc),
            )
            db.add(c)
            await db.flush()
        customers.append(c)

        v = (
            await db.execute(
                select(Vehicle).where(Vehicle.tenant_id == tid, Vehicle.vin == vin)
            )
        ).scalar_one_or_none()
        if not v:
            v = Vehicle(
                tenant_id=tid,
                customer_id=c.id,
                vin=vin,
                make=make,
                model=model,
                model_year=2018,
                mileage=62000,
                registration=reg,
            )
            db.add(v)
            await db.flush()
        vehicles.append(v)

        score = (
            await db.execute(
                select(CustomerGarageScore).where(CustomerGarageScore.customer_id == c.id)
            )
        ).scalar_one_or_none()
        if not score:
            db.add(
                CustomerGarageScore(
                    tenant_id=tid,
                    customer_id=c.id,
                    clv_score=72,
                    reliability_score=88,
                    score_metadata={"segment": "loyal"},
                )
            )

    # Bookings
    bookings = []
    if services and mechanics and bays and customers:
        b = Booking(
            tenant_id=tid,
            customer_id=customers[0].id,
            staff_id=mechanics[0][0].id,
            resource_id=bays[0].id,
            service_id=services[0].id,
            customer_name=f"{customers[0].first_name} {customers[0].last_name}",
            customer_email=customers[0].email,
            service_description=services[0].name,
            booking_date=today + timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(10, 0),
            duration_minutes=60,
            status="confirmed",
            manage_token=secrets.token_urlsafe(32),
        )
        db.add(b)
        await db.flush()
        bookings.append(b)

        db.add(
            BookingSessionService(
                tenant_id=tid,
                booking_id=b.id,
                service_id=services[0].id,
                sort_order=0,
                duration_minutes=60,
            )
        )
        if len(services) > 1:
            db.add(
                BookingSessionService(
                    tenant_id=tid,
                    booking_id=b.id,
                    service_id=services[1].id,
                    sort_order=1,
                    duration_minutes=30,
                )
            )

        db.add(
            BookingResourceAllocation(
                tenant_id=tid,
                booking_id=b.id,
                resource_id=bays[0].id,
                allocated_from=datetime.combine(b.booking_date, b.start_time, tzinfo=timezone.utc),
                allocated_to=datetime.combine(b.booking_date, time(10, 30), tzinfo=timezone.utc),
            )
        )

        if parts:
            db.add(
                BookingPartsReservation(
                    tenant_id=tid,
                    booking_id=b.id,
                    part_id=parts[0].id,
                    quantity_reserved=1,
                    status="reserved",
                )
            )
            db.add(
                VehiclePartsUsage(
                    tenant_id=tid,
                    vehicle_id=vehicles[0].id,
                    part_id=parts[0].id,
                    booking_id=b.id,
                    quantity=1,
                )
            )

    # Invoice template + sample invoice
    tpl = (
        await db.execute(
            select(IndustryInvoiceTemplate).where(
                IndustryInvoiceTemplate.tenant_id == tid,
                IndustryInvoiceTemplate.name == "Standard service invoice",
            )
        )
    ).scalar_one_or_none()
    if not tpl:
        db.add(
            IndustryInvoiceTemplate(
                tenant_id=tid,
                vertical="garage",
                name="Standard service invoice",
                template_body={
                    "line_items": [
                        {
                            "description": "Labour — diagnostics",
                            "quantity": 1,
                            "unit_price_pence": 7500,
                            "line_kind": "labor",
                        },
                        {
                            "description": "Oil filter",
                            "quantity": 1,
                            "unit_price_pence": 1560,
                            "line_kind": "part",
                        },
                    ]
                },
                is_default=True,
            )
        )

    inv = (
        await db.execute(
            select(Invoice).where(
                Invoice.tenant_id == tid, Invoice.invoice_number == "INV-GARAGE-001"
            )
        )
    ).scalar_one_or_none()
    if not inv and customers:
        inv = Invoice(
            tenant_id=tid,
            customer_id=customers[0].id,
            invoice_number="INV-GARAGE-001",
            public_token=secrets.token_urlsafe(32),
            title="MOT + interim service",
            status="sent",
            subtotal_pence=20000,
            vat_pence=4000,
            total_pence=24000,
            currency="gbp",
            booking_id=bookings[0].id if bookings else None,
        )
        db.add(inv)
        await db.flush()
        db.add(
            InvoiceItem(
                invoice_id=inv.id,
                description="MOT test",
                quantity=1,
                unit_price_pence=5495,
                vat_rate=20,
                line_total_pence=5495,
                line_kind="service",
            )
        )
        db.add(
            InvoiceItem(
                invoice_id=inv.id,
                description="Brake pads (parts)",
                quantity=1,
                unit_price_pence=6075,
                vat_rate=20,
                line_total_pence=6075,
                line_kind="part",
            )
        )
        db.add(
            InvoiceTip(tenant_id=tid, invoice_id=inv.id, amount_pence=500, method="card")
        )
        db.add(
            InvoiceWarranty(
                tenant_id=tid,
                invoice_id=inv.id,
                warranty_months=12,
                terms="Parts and labour — 12 months or 12,000 miles.",
            )
        )
        if vehicles:
            db.add(
                VehicleServiceRecord(
                    tenant_id=tid,
                    vehicle_id=vehicles[0].id,
                    booking_id=bookings[0].id if bookings else None,
                    service_date=today - timedelta(days=30),
                    description="Previous MOT",
                    mileage_at_service=58000,
                )
            )
            db.add(
                MaintenancePrediction(
                    tenant_id=tid,
                    vehicle_id=vehicles[0].id,
                    prediction_type="brake_check",
                    due_date=today + timedelta(days=90),
                    confidence=78,
                    notes="Based on mileage and last brake service",
                )
            )

    pkg = (
        await db.execute(
            select(IndustryServicePackage).where(
                IndustryServicePackage.tenant_id == tid,
                IndustryServicePackage.name == "Annual service plan",
            )
        )
    ).scalar_one_or_none()
    if not pkg:
        db.add(
            IndustryServicePackage(
                tenant_id=tid,
                name="Annual service plan",
                sessions_included=2,
                price_pence=19900,
                valid_days=365,
            )
        )

    return {
        "customers": len(customers),
        "vehicles": len(vehicles),
        "parts": len(parts),
        "bookings": len(bookings),
        "services": len(services),
    }
