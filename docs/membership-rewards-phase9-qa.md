# Membership & Rewards — Phase 9: QA

**Feature code:** `membership_rewards` on `tenant_addons`  
**Migrations:** `039_membership_rewards_core`, `041_loyalty_customer_portal`  
**Public URL:** `/p/{tenant}/memberships` (alias `/p/{tenant}/loyalty`)  
**Customer PWA:** `/rewards/{tenant}`  
**Dashboard:** `/dashboard/membership-rewards` (alias `/dashboard/loyalty`)

---

## Scope (in)

| Area | Verified |
|------|----------|
| 7-day trial on tenant signup | `test_membership_rewards.py` |
| Entitlement gate (`require_membership_rewards`) | Dashboard + integration tests |
| **Public hard-stop when trial expired** | `test_membership_rewards_phase7.py` |
| Core engines (earn / redeem / tiers / expiration) | Phase 2 tests |
| Customer portal auth + PWA API | Phase 4 tests |
| Booking auto-provisioning + widget checkbox | Phase 5 tests |
| Staff QR scan + check-in points | Phase 6 tests |
| Stripe checkout + webhook sync / revoke | Phase 7 tests |
| Landing aliases + rewards wallet embeds | Phase 8 tests |
| Tenant plans, subscriptions, ledger, tiers | Phases 1–3 tests |
| `/addons/status` includes `membership_rewards` | Phase 7 tests |

## Out of scope

| Item | Notes |
|------|--------|
| Salon industry `POST /addons/billing/memberships` | Parallel product — unchanged |
| Stripe Connect for customer membership billing | Tenant pays SaaS add-on only |
| Full Playwright / Lighthouse PWA audit | Manual optional |

---

## Automated test run

```bash
cd apps/api
python -m pytest \
  tests/test_membership_rewards.py \
  tests/test_membership_rewards_phase2.py \
  tests/test_membership_rewards_phase3.py \
  tests/test_membership_rewards_phase3_dashboard.py \
  tests/test_membership_rewards_phase4.py \
  tests/test_membership_rewards_phase5.py \
  tests/test_membership_rewards_phase6.py \
  tests/test_membership_rewards_phase7.py \
  tests/test_membership_rewards_phase8.py \
  tests/test_membership_rewards_integration.py \
  -q
```

**Expected:** **30 tests passing** (verified Phase 9).

---

## Manual UI checklist

### Signup & trial

- [ ] Register new tenant → open `/dashboard/membership-rewards` without upgrade
- [ ] Trial banner shows days remaining
- [ ] Day-6 urgency modal when `show_urgency_modal`
- [ ] `/dashboard/membership-rewards/upgrade` shows Stripe CTA
- [ ] After trial expiry: public `/p/{tenant}/memberships` returns 404; dashboard gated

### Dashboard

- [ ] Overview, analytics, customers, plans, subscriptions, rewards, tiers, settings, landing
- [ ] **Scan member QR** at `/dashboard/membership-rewards/scan`
- [ ] Alias `/dashboard/loyalty` redirects correctly

### Customer PWA

- [ ] `/rewards/{tenant}/login` — magic link + password
- [ ] Dashboard, rewards redeem, history, profile, in-store QR
- [ ] Magic link from welcome email opens verify flow

### Public page

- [ ] `/p/{tenant}/memberships` and alias `/p/{tenant}/loyalty`
- [ ] Rewards wallet section + QR when entitled
- [ ] Interest form → CRM lead; loyalty tier enroll

### Cross-links

- [ ] Booking widget QR cards (booking, refer, review, memberships, rewards wallet)
- [ ] Leads page membership/rewards link banner
- [ ] Site builder shows memberships + rewards wallet URLs

### Stripe (staging)

- [ ] `STRIPE_PRICE_MEMBERSHIP_REWARDS` set on API
- [ ] Checkout → `billing_source: stripe`, `expires_at` cleared
- [ ] Subscription cancel → add-on revoked, APIs return 403

---

## Deploy checklist

1. `cd apps/api && alembic upgrade head` (includes `041`)
2. API env: `STRIPE_PRICE_MEMBERSHIP_REWARDS`, `FRONTEND_URL`
3. Stripe webhooks: `checkout.session.completed`, `customer.subscription.*`
4. Restart API + worker (trial reminder cron)
5. Build web: `cd apps/web && pnpm build`
6. Build loyalty PWA (or proxy `/rewards` to loyalty-pwa service)
7. Nginx: route `/rewards/*` → loyalty-pwa; `/p/*/loyalty` works via web app

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Dev | | | 30/30 automated tests green |
| QA | | | Manual checklist above |
| Product | | | Trial + upgrade copy approved |
