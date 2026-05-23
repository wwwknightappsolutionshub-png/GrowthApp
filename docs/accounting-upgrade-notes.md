# Accounting Add-On — Product Decisions & Alignment

**Status:** v1 implemented on branch (migration `034_accounting_addon`).

---

## Confirmed decisions (May 2026)

| # | Decision |
|---|----------|
| 1 | **All tenants** get basic quotes & invoices: create, read, update, delete (draft). No add-on gate for this tier. |
| 2 | **Accounting add-on** activation: Stripe subscription item **and** super-admin manual grant. |
| 3 | **“Job” linkage:** both **Deal** (CRM pipeline) and **Booking** (completed / billable bookings). |
| 4 | **v1 scope** includes **expenses** and **recurring invoices** (not deferred). |
| 5 | **Currency:** UK / **GBP-only** in v1. |

---

## Tier split

### Included for every tenant (baseline)

- Quotes & invoices CRUD (API: `/api/v1/quotes`, `/api/v1/invoices`)
- List / get / send quote
- Manual mark invoice paid
- Public quote accept → auto-invoice
- Links to `customer_id`, optional `deal_id`
- VAT line rates (default 20%), totals in pence

### Accounting add-on (paid)

- Email/SMS send, reminders, viewed tracking
- Stripe payment collection on invoices
- Expenses, recurring schedules
- Extended cashflow dashboard (net of expenses)
- UK tax summaries & accountant export pack
- CRM customer financial tab
- Booking → auto-invoice

---

## Existing codebase anchors

| Area | Path |
|------|------|
| Core models | `apps/api/app/modules/quotes_invoices/` |
| Dashboard aggregates | `apps/api/app/modules/money/router.py` |
| SaaS billing (do not mix) | `apps/api/app/modules/billing/` |
| Web hub | `/dashboard/accounts`, `/dashboard/quotes`, `/dashboard/invoices` |
| Stripe adapter | `apps/api/app/adapters/payment/stripe.py` |
| Booking payments | `apps/api/app/modules/booking/enterprise/payments.py` |

---

## Suggested entitlement model (add-on)

- Table: `tenant_addons` (`feature_code='accounting'`, `status`, Stripe refs)
- Dependency: `require_accounting()` on advanced routes only
- Baseline CRUD remains on `quotes_invoices` router without gate

---

## v1 implementation phases (after **Start**)

1. **A** — `tenant_addons` + Stripe + admin grant + upsell UI  
2. **B** — Invoice send, public pay page, webhooks → paid, reminders  
3. **C** — Quote viewed; deal + booking auto-invoice hooks  
4. **D** — Expenses + dashboard net cashflow  
5. **E** — CRM customer financials  
6. **F** — Recurring invoices (+ optional auto-charge)  
7. **G** — Exports & UK tax / accountant pack  
