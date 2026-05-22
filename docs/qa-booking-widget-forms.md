# Booking Widget & QR — QA Checklist

## Prerequisites

- Migration `033_booking_widget_forms` applied
- Tenant has optional **Google Business** connected (Integrations) for QR C
- Active **approved** tradesman referral program with `tenant_id` in rules for QR B rewards

## QR A — Public booking (form builder)

- [ ] Super Admin → **Booking Forms** — edit category template, save
- [ ] Tenant → **Bookings → Widget** → **Edit booking form (QR A)** — customise, save
- [ ] Public `/book/{slug}` renders dynamic fields from schema
- [ ] Submit creates booking + CRM customer/lead

## QR B — Refer & Win

- [ ] `/book/{slug}/refer` shows five fields
- [ ] Submit creates lead in pipeline stage **New** (`source=refer_win_qr`)
- [ ] Referrer upserted in **Customers**; `ref_count` increments
- [ ] `reward_*` + `referral_program_id` set when active program exists

## QR C — Review & Comments

- [ ] With GMB connected: `/book/{slug}/rate` redirects to Google review URL
- [ ] Without GMB: clear error message (no mock form)
- [ ] `tenant.google_review_url` used when set

## Widget hub

- [ ] Three QRs with labels: Booking, Refer & Win, Review & Comments
- [ ] URLs distinct (`/book/...`, `/book/.../refer`, `/book/.../rate`)

## API smoke

```bash
cd apps/api && pytest tests/test_booking_widget_forms.py tests/test_booking_production.py -q
```
