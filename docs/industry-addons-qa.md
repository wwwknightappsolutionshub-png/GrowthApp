# Industry Add-ons QA — Salon & Garage

## Garage demo tenant (pre-seeded)

Run once (idempotent):

```bash
cd apps/api
.venv\Scripts\python.exe scripts/seed_garage_addons.py
```

| Field | Value |
|-------|--------|
| **Email** | `garage@knightmotors.co.uk` |
| **Password** | `Garage@Test1` |
| **Business** | Knight Motors Garage |
| **Vertical** | `garage` (default settings in `tenant_industry_profile`) |
| **Add-ons** | All three granted (`industry_booking`, `industry_billing`, `industry_crm`) |

Includes sample parts, vehicles, mechanics, bays, bookings, invoices, warranties, and CRM scores.

## Local preview

1. Start API: `cd apps/api && .venv\Scripts\uvicorn app.main:app --reload --port 8000`
2. Start web: `cd apps/web && pnpm dev`
3. Log in with the garage demo credentials above (or any salon/garage tenant)
4. Open **Industry Add-ons** in the sidebar — no need to click **Grant all** for the demo garage user
5. Switch vertical **Salon** / **Garage** on other tenants via the workspace toggles

## URLs

| Page | Path |
|------|------|
| Hub | `/dashboard/addons` |
| Booking | `/dashboard/addons/booking` |
| Billing | `/dashboard/addons/billing` |
| CRM | `/dashboard/addons/crm` |

## API coverage (all require entitlement)

### Salon booking
- [ ] `POST /addons/booking/sessions` multi-service
- [ ] `GET /addons/booking/staff/match`
- [ ] `POST /addons/booking/allocate-resource`
- [ ] `GET /addons/booking/gap-fill`
- [ ] `POST /addons/booking/{id}/upsells`

### Garage booking
- [ ] `GET /addons/booking/estimate-duration`
- [ ] `GET /addons/booking/mechanics/match`
- [ ] `POST /addons/booking/parts`
- [ ] `POST /addons/booking/{id}/check-parts`
- [ ] `POST /addons/booking/vehicles`

### Salon billing
- [ ] `POST /addons/billing/invoices/combo` (service + product lines)
- [ ] `POST /addons/billing/tips`
- [ ] `POST /addons/billing/memberships`
- [ ] `POST /addons/billing/packages`

### Garage billing
- [ ] `POST /addons/billing/templates`
- [ ] `POST /addons/billing/markup-rules`
- [ ] `POST /addons/billing/warranties`
- [ ] `GET /addons/billing/vin/{vin}/invoices`

### Salon CRM
- [ ] `PUT /addons/crm/salon/profile`
- [ ] `POST /addons/crm/salon/media`
- [ ] `POST /addons/crm/salon/rebook/{customer_id}`
- [ ] `GET /addons/crm/salon/segments`

### Garage CRM
- [ ] `GET /addons/crm/garage/vehicles/{id}/history`
- [ ] `POST /addons/crm/garage/vehicles/{id}/predictions`
- [ ] `POST /addons/crm/garage/customers/{id}/scores`

## Automated tests

```bash
cd apps/api && .venv\Scripts\python.exe -m pytest tests/test_industry_salon_garage.py tests/test_addons_entitlement.py -q
```

## Migrations

```bash
cd apps/api && .venv\Scripts\alembic upgrade head
```

Requires `035_industry_addons_core` and `036_industry_salon_garage`.
