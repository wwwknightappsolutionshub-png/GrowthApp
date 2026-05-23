# Industry Add-Ons — Phase 1 Architecture

**Status:** Salon + Garage Phases 3–8 implemented (Realtor deferred).  
**Scope:** Three paid tools × Salon + Garage verticals (Realtor not in v1).  
**Baseline:** Reuse `tenant_addons`, enterprise booking (`026+`), CRM enterprise (`028+`), accounting (`034`).

---

## Product model

| Add-on SKU (`feature_code`) | Tool | Gated routes / UI |
|-----------------------------|------|-------------------|
| `industry_booking` | Enhanced Booking & Scheduling | `/api/v1/addons/booking/*`, `/dashboard/addons/booking/*` |
| `industry_billing` | Industry-Smart Billing & Invoicing | `/api/v1/addons/billing/*`, extends quotes/invoices when entitled |
| `industry_crm` | Smart Customer / Job History CRM | `/api/v1/addons/crm/*`, customer/deal/vehicle panels |

**Vertical** (behaviour branch, not a separate Stripe SKU):

| `vertical` | Maps from `tenants.business_type` | Override |
|------------|-----------------------------------|----------|
| `salon` | beautician, salon, barber, spa, … | `tenant_industry_profile.vertical` |
| `realtor` | estate agent, realtor, property, … | same |
| `garage` | garage, mechanic, auto, MOT, … | same |

Tenant may buy 1–3 tools; each tool activates only its feature flag. UI and API **must** call `require_addon("industry_*")` and return upgrade payload when false.

---

## Non-negotiable gating rules

1. **Backend:** Every industry route uses `Depends(require_addon(FEATURE_*))`.
2. **Frontend:** `useAddonEntitlement(code)` — hide nav items; render `<AddonUpgradeScreen feature={...} />` on direct URL.
3. **Workers:** Cron jobs check `tenant_has_addon` before industry automation.
4. **No leakage:** List endpoints for baseline booking/CRM must not embed industry-only fields unless entitled (use separate DTOs or `Industry*Response` optional blocks).

---

## Tool 1 — Enhanced Booking (by vertical)

### Salon / Beautician

| Feature | Data | API (v1) |
|---------|------|----------|
| Multi-service session | `booking_session_services` (booking_id, service_id, order, duration) | `POST /addons/booking/sessions` |
| Staff skill match | `staff_skills`, `service_required_skills` | `GET /addons/booking/staff/match` |
| Booth/room allocation | extend `booking_resources` usage | `POST /addons/booking/allocate-resource` |
| Gap-fill optimization | `slot_suggestions` service | `GET /addons/booking/gap-fill` |
| Product upsells at checkout | `booking_upsell_lines` | `POST /addons/booking/{id}/upsells` |

### Realtor

| Feature | Data | API |
|---------|------|-----|
| Property calendar | `properties`, `property_availability` | CRUD `/addons/booking/properties` |
| Multi-client showings | `showing_groups`, `showing_attendees` | `POST /addons/booking/showings` |
| Auto disclosure docs | `property_documents`, email template | `POST /addons/booking/showings/{id}/disclosures` |
| Drive-time scheduling | `showing_travel_matrix` (cached legs) | `POST /addons/booking/schedule/drive-aware` |
| Open-house bulk | `open_house_events` | `POST /addons/booking/open-houses` |

### Garage

| Feature | Data | API |
|---------|------|-----|
| Vehicle service time estimate | `vehicle_service_estimates` (make/model/service → minutes) | `GET /addons/booking/estimate-duration` |
| Mechanic specialization | `mechanic_skills`, match on booking | `GET /addons/booking/mechanics/match` |
| Bay allocation | `booking_resources.resource_type=bay` | same as salon allocation |
| Parts stock check | `parts_inventory`, `booking_parts_reservations` | `POST /addons/booking/{id}/check-parts` |

**Extends:** `booking/enterprise/*` slots, services, resources — industry module wraps/strategies.

---

## Tool 2 — Industry-Smart Billing (by vertical)

Builds on **baseline** quotes/invoices (all tenants) + **accounting** add-on where overlap (Stripe send, recurring).

### Salon

| Feature | Tables | Notes |
|---------|--------|-------|
| Service + product combo | `invoice_line_items.kind` = service\|product | |
| Tipping workflow | `invoice_tips`, `payment_tip_allocations` | post-checkout tip |
| Memberships | `memberships`, `membership_benefits` | links recurring |
| Packages | `service_packages`, `package_redemptions` | e.g. monthly facial |

### Realtor

| Feature | Tables |
|---------|--------|
| Commission per property | `listing_commissions`, `commission_splits` |
| Marketing expense per listing | `listing_marketing_expenses` |
| Rent-management fee auto-invoice | `rent_management_schedules` |
| Lawyer/notary/referral billing | `referral_fee_invoices` |

### Garage

| Feature | Tables |
|---------|--------|
| Parts + labor templates | `invoice_templates` (vertical=garage) |
| Parts markup rules | `parts_markup_rules` (percent by category) |
| Warranty per invoice | `invoice_warranties` |
| VIN history | `vehicles`, `vehicle_service_records` |

---

## Tool 3 — Smart Customer / Job History CRM (by vertical)

Extends CRM enterprise (`customers`, `deals`, `crm_activities`, segments).

### Salon

| Feature | Tables |
|---------|--------|
| Stylist notes (formula, allergies) | `customer_salon_profile` (jsonb formula, allergies text) |
| Photo timeline | `customer_media_timeline` |
| Rebook reminders | worker + `crm_automation_rules` |
| Segmentation | existing `segments` + salon tags |

### Realtor

| Feature | Tables |
|---------|--------|
| Buyer profile matching | `buyer_profiles`, `buyer_preferences` |
| Showing history | `showing_activity_log` |
| Post-showing follow-ups | automation rules |
| Property interest score | `buyer_property_scores` |

### Garage

| Feature | Tables |
|---------|--------|
| Repair history | `vehicle_service_records` |
| Predictive maintenance | `maintenance_predictions` |
| Parts usage per vehicle | `vehicle_parts_usage` |
| CLV + reliability score | `customer_garage_scores` |

---

## Database — migration plan

| Migration | Contents |
|-----------|----------|
| `035_industry_addons_core` | `tenant_industry_profile`, indexes on `tenant_addons` (no change), addon metadata |
| `036_industry_booking` | Session services, skills, showings, properties, vehicles (shared), parts inventory |
| `037_industry_billing` | Tips, memberships, packages, commissions, listings, warranties, VIN |
| `038_industry_crm` | Vertical profile extensions, media timeline, buyer/garage scores, predictions |

**Shared entities (cross-vertical):**

```
tenant_industry_profile (tenant_id PK, vertical, settings jsonb)
vehicles (tenant_id, customer_id, vin, make, model, year, mileage)
properties (tenant_id, address, listing_status, ...)  -- realtor
parts_inventory (tenant_id, sku, qty, unit_cost_pence, ...)
staff_skills / service_required_skills / mechanic_skills
booking_session_services, booking_upsell_lines, showing_groups, open_house_events
```

---

## API layout

```
/api/v1/addons/status                          GET  — all three flags + vertical
/api/v1/addons/checkout                        POST — Stripe (metadata feature_code)
/api/v1/addons/booking/...                     *    — require industry_booking
/api/v1/addons/billing/...                     *    — require industry_billing
/api/v1/addons/crm/...                         *    — require industry_crm
/api/admin/tenants/{id}/addons/{feature_code}  POST — grant|revoke (extend existing)
```

Public routes stay under `/api/v1/public/`; industry-only public flows (e.g. open-house RSVP) gated by tenant addon + slug.

---

## File structure

```
apps/api/app/modules/addons/
  common/
    constants.py          # FEATURE_INDUSTRY_*, Vertical enum
    entitlement.py        # tenant_has_addon, require_addon
    models.py             # TenantIndustryProfile (Phase 2 migration)
    router.py             # /addons/status, checkout stubs
    schemas.py
    vertical.py           # resolve_vertical(tenant)
  verticals/
    salon/
      booking/service.py, router.py, schemas.py
      billing/...
      crm/...
    realtor/...
    garage/...
  registry.py             # vertical → strategy classes

apps/web/
  app/(dashboard)/dashboard/addons/
    page.tsx                # hub: 3 cards, locked/unlocked
    booking/page.tsx
    billing/page.tsx
    crm/page.tsx
    upgrade/page.tsx
  components/addons/
    AddonUpgradeScreen.tsx
    AddonGate.tsx
  lib/addons.ts             # api client + useAddonEntitlement
```

---

## Frontend gating

```tsx
// Sidebar: only if status.industry_booking
{entitled('industry_booking') && <NavItem href="/dashboard/addons/booking" />}

// Page
if (!entitled('industry_booking')) return <AddonUpgradeScreen feature="industry_booking" />
```

---

## Implementation phases (after Phase 1)

| Phase | Deliverable | Tests |
|-------|-------------|-------|
| **2** | `035` migration + entitlement API + upgrade UI + admin grant | `test_addons_entitlement.py` |
| **3** | Salon booking (multi-service, skills, resources, gap-fill, upsells) | booking integration |
| **4** | Salon billing + CRM | billing + crm tests |
| **5** | Realtor booking + billing + CRM | drive-time, showings, commissions |
| **6** | Garage booking + billing + CRM | VIN, parts, bay, warranty |
| **7** | Workers (reminders, gap-fill cron, maintenance predictions) | worker tests |
| **8** | UAT scripts + QA checklist | `docs/industry-addons-qa.md` |

**Estimate:** ~8–12 weeks for full production parity across 3 verticals × 3 tools; parallelize verticals after Phase 2.

---

## Stripe & admin

Mirror accounting:

- `STRIPE_PRICE_INDUSTRY_BOOKING`, `STRIPE_PRICE_INDUSTRY_BILLING`, `STRIPE_PRICE_INDUSTRY_CRM`
- Webhook `checkout.session.completed` → `grant_addon(feature_code)`
- Admin: `POST /api/admin/tenants/{id}/addons/{feature_code}` body `{ "action": "grant"|"revoke" }`

---

## Quality bar

- **Unit:** entitlement, vertical resolver, pricing/markup calculators
- **Integration:** each API module with test tenant + grant
- **Permission:** 403 without addon; 200 with grant
- **UAT:** per-vertical playbook in `docs/industry-addons-qa.md` (Phase 8)

---

## Dependencies on existing modules

| Existing | Industry add-on uses |
|----------|---------------------|
| `tenant_addons` | Entitlement (same table, new `feature_code`s) |
| `booking/enterprise` | Slots, services, resources, staff |
| `quotes_invoices` | Line items, invoices (billing tool) |
| `accounting` | Optional: Stripe send, recurring for memberships |
| `crm/enterprise` | Pipelines, activities, segments |
| `segments` | Salon/realtor segmentation |

Do **not** mix `billing.BillingInvoice` (SaaS subscription) with tenant CRM invoices.

---

## Phase 1 deliverables checklist

- [x] Architecture plan (this document)
- [x] File structure + shared entitlement scaffold
- [x] Database schema design (migrations 035–038 outlined)
- [x] API endpoint map
- [x] UI layout plan (`/dashboard/addons/*`)
- [x] Salon + Garage backend/frontend (Phases 3–8)
- [x] Integration tests (`test_industry_salon_garage.py`, `test_addons_entitlement.py`)
- [ ] Realtor vertical (deferred)
- [ ] Stripe checkout for industry SKUs (production billing)

**Next step:** Phase 2 — run `035_industry_addons_core` migration, wire `/api/v1/addons/status`, upgrade screens, admin grant for three feature codes.
