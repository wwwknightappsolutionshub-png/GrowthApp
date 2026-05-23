# Membership & Rewards — Phase 8: QA

**Feature code:** `membership_rewards` on `tenant_addons`  
**Migration:** `039_membership_rewards_core`  
**Public URL:** `/p/{tenant}/memberships`  
**Dashboard:** `/dashboard/membership-rewards`

---

## Scope (in)

| Area | Verified |
|------|----------|
| 7-day trial on tenant signup | `test_membership_rewards.py` |
| Entitlement gate (`require_membership_rewards`) | Phase 1 + integration tests |
| Tenant plans (`mr_membership_plans`) | CRUD + auto-landing sync |
| Customer subscriptions | Create / list / cancel |
| Points ledger (separate from referral cash) | Earn hooks + adjust + redeem |
| Loyalty tiers + leaderboard | Bootstrap tiers on grant |
| Landing auto-publish + regenerate | Phase 5 tests |
| Public page + interest → CRM lead | Integration smoke |
| Trial reminders (day 3 / 6 / 15) | Phase 6 tests + cron 09:15 & 18:15 |
| Stripe checkout + webhook activation | Phase 7 tests |
| `/addons/status` includes `membership_rewards` | Phase 7 tests |
| Dashboard UI sections | Manual checklist below |

## Out of scope (not in this module)

| Item | Notes |
|------|--------|
| Renaming salon `memberships` (industry billing) | Unchanged — parallel product |
| Replacing `referrals` cash payouts | Points only; referrals module unchanged |
| Stripe Connect for **customer** membership billing | Tenant plans are manual/subscription records; tenant pays SaaS add-on SKU |
| Mobile PWA install flows | Unrelated |

---

## Automated test run

```bash
cd apps/api
python -m pytest \
  tests/test_membership_rewards.py \
  tests/test_membership_rewards_phase3.py \
  tests/test_membership_rewards_phase5.py \
  tests/test_membership_rewards_phase6.py \
  tests/test_membership_rewards_phase7.py \
  tests/test_membership_rewards_integration.py \
  -q
```

**Expected:** 18 tests passing (as of Phase 8).

---

## Manual UI checklist

### Signup & trial

- [ ] Register new tenant → open `/dashboard/membership-rewards` without upgrade
- [ ] Trial banner shows days remaining
- [ ] Day-6 urgency modal appears when `show_urgency_modal` (or simulate via DB / cron)
- [ ] `/dashboard/membership-rewards/upgrade` shows Stripe CTA (or “not configured” if no price ID)

### Dashboard (`/dashboard/membership-rewards`)

- [ ] Overview cards load (`GET /membership-rewards/dashboard`)
- [ ] **Plans:** create plan → appears in list; first plan triggers landing sync
- [ ] **Subscriptions:** assign customer to plan; cancel works
- [ ] **Rewards:** add catalog item; redeem from customer loyalty (if UI wired)
- [ ] **Loyalty:** leaderboard loads; manual points adjust
- [ ] **Landing:** edit copy, regenerate, publish; public URL shown in status

### Public page (`/p/{tenant}/memberships`)

- [ ] 404 when landing not published
- [ ] Published page shows plans and CTA
- [ ] Interest form submits → lead with `source: memberships_page` (CRM)

### Add-ons hub (`/dashboard/addons`)

- [ ] Membership card shows **Active** when entitled
- [ ] Industry add-ons unchanged

### Site builder

- [ ] Business site status includes `memberships_url` when published

### Stripe (staging)

- [ ] `STRIPE_PRICE_MEMBERSHIP_REWARDS` set on API
- [ ] Checkout completes → `has_membership_rewards` stays true, `expires_at` cleared, `billing_source: stripe`
- [ ] Cancel subscription in Stripe → add-on revoked (dashboard gated)

### Admin

- [ ] `POST /admin/tenants/{id}/addons/membership-rewards` grant/revoke

---

## Regression

- [ ] Salon industry `POST /addons/billing/memberships` still works (different tables)
- [ ] Legacy referrals module removed; loyalty points only via `mr_points_ledger`
- [ ] Accounting add-on `tenant_addons` rows independent of `membership_rewards`
- [ ] Tenant isolation: user A cannot read tenant B membership data

---

## Deploy checklist

1. `alembic upgrade head` (includes `039_membership_rewards_core`)
2. Set env on API:
   - `STRIPE_PRICE_MEMBERSHIP_REWARDS=price_...`
   - `FRONTEND_URL=https://app.yourdomain.com`
3. Stripe webhook events: `checkout.session.completed`, `customer.subscription.*`
4. Restart API + ARQ worker (trial reminder cron)
5. Rebuild/restart web

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Dev | | | Automated suite green |
| QA | | | Manual checklist above |
| Product | | | Trial + upgrade copy approved |
