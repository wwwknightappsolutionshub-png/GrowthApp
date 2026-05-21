# Enterprise Booking Upgrade — Gap Report & Implementation Notes

**Branch:** `enterprise-booking-upgrade`  
**Migration:** `026_enterprise_booking`  
**API prefix (unchanged):** `/api/v1/bookings`, `/api/v1/public/booking/{tenant_slug}`

## Phase 1 — Gap Report (pre-upgrade baseline)

| Checklist area | Before upgrade | After upgrade |
|----------------|----------------|---------------|
| **A. Core** | CRUD + public availability/create; no widget UI | Widget config + embed script; staff/resources/services; slot generation; multi-location; self-service tokens; timezone; calendar sync connections |
| **B. Payments** | DB columns only | Stripe PaymentIntent/SetupIntent; deposits; no-show fees; prepaid; packages/credits; refunds; service fees |
| **C. Automation** | `booking_confirmed` event only | Queued SMS/email/WhatsApp reminders; follow-up/no-show/re-engagement/upsell/abandoned recovery hooks + AI recommend |
| **D. CRM** | Basic booking fields | Timeline endpoint; lead_status; intake; custom_fields; notes (existing) |
| **E. Staff/Ops** | `staff` table, no API | Staff CRUD; shifts; blackouts; resource availability; overbooking guard |
| **F. Admin** | Tenant health missed_bookings | Per-tenant settings; audit via `log_action`; business hours; GDPR export slice |
| **G. Marketing** | None | Booking link; promo codes; pixel IDs; referral hook (existing) |
| **H. Analytics** | None | Dashboard aggregates: revenue/staff, cancellations, no-show, conversion, utilization |
| **I. Performance** | Basic list pagination | Indexes on new FKs; notification queue; rate limits on public booking |

**Validation:** API uses **Pydantic v2** (project standard). Web client uses **Zod** in `apps/web/lib/booking-schemas.ts` for forms/widgets.

---

## Phase 2 — Architecture

```
apps/api/app/modules/booking/
  models.py              # Core Staff, AvailabilitySlot, Booking (+ new columns)
  enterprise_models.py   # Settings, services, resources, packages, queue, etc.
  schemas.py             # Backward-compatible booking schemas
  enterprise_schemas.py  # Enterprise request/response models
  service.py             # Core booking (extended)
  enterprise/            # Domain services
    settings.py
    staff.py
    slots.py
    payments.py
    automation.py
    analytics.py
    calendar_sync.py
    packages.py
    marketing.py
  router.py              # Includes enterprise_router
  enterprise_router.py   # /bookings/* enterprise endpoints
```

**Workers:** `apps/api/app/workers/tasks/booking_notifications.py`  
- Cron: process `booking_notification_queue`, send reminders, abandoned recovery nudges

**Public:** Extended routes under `/api/v1/public/booking/...`  
- Widget config, payment intent, manage (reschedule/cancel) by token

---

## Backward compatibility

- Existing `GET/POST/PATCH /api/v1/bookings` payloads unchanged; new fields optional on responses.
- `POST /api/v1/public/booking/{tenant_slug}` unchanged; optional new fields accepted.
- Cancel releases `availability_slots.is_booked` when `slot_id` present.

---

## Configuration (env)

| Variable | Purpose |
|----------|---------|
| `PAYMENT_PROVIDER` | `stripe` or `mock` for booking deposits |
| `STRIPE_SECRET_KEY` | PaymentIntent creation |
| `FRONTEND_URL` | Manage-booking + widget redirect URLs |

---

## Tenant UI (web)

| Path | Purpose |
|------|---------|
| `/dashboard/bookings` | List + filters + link to settings |
| `/dashboard/bookings/settings` | Deposits, fees, automation, hours, pixels |
| `/dashboard/bookings/staff` | Staff + shifts + blackouts |
| `/dashboard/bookings/analytics` | Enterprise analytics dashboard |
| `/dashboard/bookings/widget` | Embed code + booking link |
| `/book/{tenant_slug}` | Public booking widget page |
| `/public/booking/manage/{token}` | Self-service reschedule/cancel |

---

## Tests

- `apps/api/tests/test_booking_enterprise.py` — settings, staff, slots, public manage token, analytics

---

## Remaining / future hardening

- Full Google Calendar OAuth UI (connections table + stub sync implemented; OAuth flow uses integrations pattern).
- Outlook Graph API (iCal export implemented; Graph push optional).
- WhatsApp template approval per tenant (queues message; delivery via existing WhatsApp module).
- E2E Playwright for widget (optional CI add-on).

---

## Changelog (this branch)

### Delivered

- **Migration `026_enterprise_booking`**: extended `bookings`, `staff`, `availability_slots`; new tables for settings, services, resources, shifts, blackouts, packages, credits, promos, calendar connections, notification queue, abandoned sessions.
- **API**: 40+ new routes under `/api/v1/bookings/*` (settings, staff, slots, payments, packages, promos, analytics, calendar, export).
- **Public**: widget config, rate-limited booking, manage token reschedule/cancel, iCal feed.
- **Workers**: `process_booking_notification_queue` cron every 10 minutes.
- **Payments**: Stripe/mock `PaymentIntent`, `SetupIntent`, refunds on booking adapter.
- **Web**: settings, staff, analytics, widget pages; `/book/{slug}`; `/book/manage/{token}`; embed script `/embed/booking-widget.js`.
- **Zod**: `apps/web/lib/booking-schemas.ts` for client validation.
- **Tests**: `apps/api/tests/test_booking_enterprise.py` (5 passing).

### Deploy steps

```bash
cd apps/api && .venv/bin/alembic upgrade head
sudo systemctl restart customerflow-api customerflow-worker
cd apps/web && pnpm build && sudo systemctl restart customerflow-web
```

### API quick reference

| Method | Path |
|--------|------|
| GET/PATCH | `/api/v1/bookings/settings` |
| GET | `/api/v1/bookings/link` |
| GET/POST | `/api/v1/bookings/services`, `/resources`, `/staff` |
| POST | `/api/v1/bookings/slots/generate` |
| POST | `/api/v1/bookings/payments/intent` |
| GET | `/api/v1/bookings/analytics` |
| GET | `/api/v1/public/booking/{slug}/widget` |
| POST | `/api/v1/public/booking/manage/{token}` |

Existing routes unchanged: `GET/POST/PATCH /api/v1/bookings`, public availability + create.

See git log on `enterprise-booking-upgrade` for file-level commits.
