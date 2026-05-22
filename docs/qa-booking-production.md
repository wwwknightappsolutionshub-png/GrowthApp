# Booking & Accounts — Production QA Checklist

Run after deploy (`alembic upgrade head`, API restart, `pnpm build` in `apps/web`).

## Accounts (in-module invoices)

- [ ] Open `/dashboard/accounts` — `TenantWelcomeHeader`, cashflow chart, module cards load
- [ ] Invoices panel lists existing invoices with status badges
- [ ] Create draft invoice (customer + amount) — appears in list
- [ ] Mark sent invoice as paid — status updates, dashboard headline refreshes
- [ ] Delete **draft** only — succeeds; non-draft shows error

## Bookings hub

- [ ] `/dashboard/bookings` — upcoming countdown shows next sessions with live-ish timers
- [ ] **+ New booking** opens form; save creates row and CRM lead/customer link
- [ ] Click booking row → detail page; edit date/slot/status with **notify customer** — email + in-app
- [ ] Hard **Delete** removes booking and frees slot
- [ ] Completed booking → **Request feedback** sends email/in-app; public `/book/feedback/{token}` works once

## Public booking & CRM

- [ ] `/book/{slug}` — branded shell, services, slots, email required
- [ ] Submit creates booking + CRM customer/lead (verify in CRM)
- [ ] If deposit enabled — deposit message shown; payment intent returned when configured

## Three QR flows

- [ ] `/dashboard/bookings/widget` — three QRs: book, refer, rate info URLs
- [ ] Scan book QR → public form
- [ ] Refer QR → `/book/{slug}/refer`
- [ ] Rate QR → `/book/{slug}/rate` (info only; real rating via token after completed visit)

## Staff enterprise

- [ ] Add / edit / deactivate staff
- [ ] Delete staff without future bookings
- [ ] Generate slots for date range
- [ ] Add blackout — blocks availability in slot generation

## API smoke (optional)

```bash
cd apps/api && pytest tests/test_booking_enterprise.py tests/test_booking_production.py -q
```

## Regression

- [ ] AI assistant still responds (OpenAI quota/billing if using live provider)
- [ ] Login and tenant dashboard load without 500s
