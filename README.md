# CustomerFlow AI — All-in-one AI Platform for UK Businesses

A production-ready, multi-tenant SaaS platform for **every UK business**: trades, hospitality, beauty, healthcare, real estate, automotive, B2B consultants, fitness and local services.

Four engines, one subscription:

- **Lead Generation** — AI landing pages, ads, outreach, lead scoring
- **Customer Retention & Loyalty** — journeys, win-back, reviews, reminders
- **Visibility & Reputation** — review flows, social AI, widgets, SEO
- **Operations & Money Intelligence** — tasks, scheduling, invoicing, cashflow

Powered by a hybrid AI router (OpenAI primary + local-LLM fallback), end-to-end multi-tenancy with Postgres RLS, and a closed-loop growth model: **Lead → CRM → Operate → Bill → Retain → Refer**.

---

## Architecture

```
GrowthApp/
├── apps/
│   ├── api/          # Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic
│   ├── web/          # Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui
│   └── worker/       # ARQ background jobs (shares api codebase)
├── infra/
│   ├── docker-compose.yml          # Production (Caddy + web + api + worker + postgres + redis)
│   ├── docker-compose.override.yml # Local dev overrides
│   ├── Caddyfile                   # Auto-HTTPS reverse proxy
│   └── scripts/                   # deploy.sh, backup.sh, generate-types.sh
└── packages/
    └── shared-types/   # TypeScript types (OpenAPI-generated)
```

---

## Quick Preview (one-shot)

Two ways to spin up a fully-seeded preview with a super-admin and four tenant
owners pre-created.

### Windows / PowerShell (SQLite, no Docker required)

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\preview.ps1
# Stop with:
pwsh scripts\preview-stop.ps1
```

### Docker Compose (Postgres + Redis + worker)

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\preview-docker.ps1
# Stop with:
cd infra; docker compose down
```

Both flows print the same credential block:

| Role | Email | Password | Lands on |
|---|---|---|---|
| Super admin | `admin@customerflow.ai` | `Admin@CustomerFlow1` | `/admin` |
| Plumber (Growth) | `mike@smithsplumbing.co.uk` | `Plumber@Test1` | `/dashboard` |
| Electrician (Pro) | `sarah@brightspark.co.uk` | `Electric@Test1` | `/dashboard` |
| Cleaner (Starter) | `priya@sparkclean.co.uk` | `Cleaner@Test1` | `/dashboard` |
| Salon (Growth) | `amira@luxesalon.co.uk` | `Salon@Test12` | `/dashboard` |
| Staff member | `dave@smithsplumbing.co.uk` | `Staff@Test123` | `/dashboard` |

Web UI: <http://localhost:3000> · API docs: <http://localhost:8000/docs>

---

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop running
- Python 3.11+ with `uv` (`pip install uv`)
- Node.js 20+ with `pnpm` (`npm i -g pnpm`)

### 1. Clone and configure environment

```bash
cd infra
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET, JWT_REFRESH_SECRET, POSTGRES_PASSWORD
```

### 2. Start all services with Docker

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

This starts: PostgreSQL, Redis, FastAPI (hot-reload), Next.js (hot-reload), ARQ Worker.

### 3. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Access the app

| Service | URL |
|---|---|
| Web Dashboard | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| API Health | http://localhost:8000/healthz |

### 5. Register your first business

Go to http://localhost:3000/register and create a test account.

---

## Local Development (without Docker)

### API

```bash
cd apps/api
uv sync
cp ../../infra/.env.example .env   # edit DATABASE_URL and REDIS_URL for local
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
cd apps/api
uv run arq app.workers.worker_settings.WorkerSettings
```

### Web

```bash
cd apps/web
pnpm install
cp .env.local.example .env.local
pnpm dev
```

---

## Production Deployment (VPS)

### Prerequisites on VPS
- Docker + Docker Compose
- Git access to this repo

### First-time setup

```bash
# On your VPS
git clone <your-repo> /opt/growthapp
cd /opt/growthapp/infra
cp .env.example .env

# Edit .env with production values:
#   - DOMAIN=yourdomain.com
#   - CADDY_EMAIL=admin@yourdomain.com
#   - POSTGRES_PASSWORD=<strong-password>
#   - JWT_SECRET=<64-char-hex>  (python -c "import secrets; print(secrets.token_hex(64))")
#   - JWT_REFRESH_SECRET=<another-64-char-hex>

docker compose up -d
docker compose exec api alembic upgrade head
```

Caddy will automatically obtain Let's Encrypt certificates for:
- `app.yourdomain.com` → Next.js dashboard
- `api.yourdomain.com` → FastAPI

### Subsequent deploys

```bash
cd /opt/growthapp/infra
./scripts/deploy.sh --migrate
```

---

## Enabling Real Integrations

All integrations default to **mock mode** — they log to stdout instead of calling external APIs. Enable them by setting env vars:

### SMS (Twilio)
```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxx
TWILIO_FROM_NUMBER=+441234567890
```

### Email (Resend)
```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxxxxxx
RESEND_FROM_EMAIL=hello@yourdomain.com
```

### Payments (Stripe)
```env
PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxx
STRIPE_PRICE_STARTER=price_xxxxxxxxx
STRIPE_PRICE_GROWTH=price_xxxxxxxxx
STRIPE_PRICE_PRO=price_xxxxxxxxx
```
Set up webhook at: `https://api.yourdomain.com/api/v1/webhooks/stripe`
Events: `customer.subscription.*`, `invoice.payment_succeeded`

### AI Content (OpenAI)
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

### Social Media (Facebook/Instagram)
```env
SOCIAL_PROVIDER=facebook
FACEBOOK_APP_ID=xxxxxxxxx
FACEBOOK_APP_SECRET=xxxxxxxxx
```

---

## Module Overview

| Module | Path | Responsibility |
|---|---|---|
| **auth** | `app/modules/auth/` | Register, login, JWT, refresh tokens, password reset |
| **tenants** | `app/modules/tenants/` | Business profile, members (RBAC), locations |
| **billing** | `app/modules/billing/` | Stripe subscriptions, plans, quota enforcement |
| **leads** | `app/modules/leads/` | Lead capture, tagging, conversion to CRM deal |
| **crm** | `app/modules/crm/` | Kanban pipeline, deals, customers, activity log |
| **booking** | `app/modules/booking/` | Calendar slots, self-booking, Stripe deposit |
| **quotes_invoices** | `app/modules/quotes_invoices/` | Quotes, invoices, payments, PDF generation |
| **automation** | `app/modules/automation/` | Trigger-based workflows, SMS/email sequences |
| **messaging** | `app/modules/messaging/` | Unified inbox (SMS + email), conversations |
| **reputation** | `app/modules/reputation/` | Review requests, smart routing, dashboard |
| **social** | `app/modules/social/` | AI post generation, FB/IG publishing |
| **audit** | `app/modules/audit/` | Append-only audit log for GDPR/compliance |
| **gdpr** | `app/modules/gdpr/` | Data export and erasure requests |
| **public** | `app/modules/public/` | Unauthenticated: lead forms, booking, review, widget |
| **webhooks** | `app/modules/webhooks/` | Stripe, Twilio inbound hooks |

---

## Key End-to-End Flows

### Lead → Booked Job
1. Visitor submits `POST /api/v1/public/leads/{tenant-slug}`
2. Lead created → automation triggers welcome SMS
3. Staff sees lead in Leads page → clicks "Add to Pipeline"
4. Deal created in "New" stage → staff moves to "Quoted"
5. Quote sent → customer accepts via `/quote/{token}`
6. Invoice raised → customer pays via Stripe link
7. Staff moves deal to "Booked"

### Completed Job → Review → Social
1. Staff moves deal to "Completed"
2. `send_review_request` job fires after 2 hours
3. Customer gets SMS → taps link → rates 5★ → **redirected to Google review URL**
4. Rates 2★ → **private feedback captured**, owner notified
5. `generate_social_post` job calls OpenAI → draft post created
6. Owner sees draft in Social tab → clicks "Approve & Post"
7. `publish_social_post` job publishes to Facebook/Instagram

### Missed Call → Recovery
1. Twilio webhook fires `POST /api/v1/webhooks/twilio/voice`
2. `handle_missed_call` job runs → SMS sent: "Sorry we missed your call..."
3. Lead created with `source=missed_call` → appears in pipeline

---

## Subscription Plans

| Plan | Price | Locations | Leads/mo | SMS/mo | Users | Social | AI |
|---|---|---|---|---|---|---|---|
| Starter | £99/mo | 1 | 500 | 1,000 | 1 | ✗ | ✗ |
| Growth | £149/mo | 3 | 2,000 | 5,000 | 5 | ✓ | ✗ |
| Pro | £199/mo | Unlimited | 10,000 | 20,000 | 20 | ✓ | ✓ |

14-day free trial, no credit card required.

---

## Running Tests

```bash
cd apps/api
uv run pytest -v
```

---

## Backup

```bash
# Manual backup
./infra/scripts/backup.sh

# Automate with cron (runs at 2am daily)
echo "0 2 * * * /opt/growthapp/infra/scripts/backup.sh >> /var/log/growthapp-backup.log 2>&1" | crontab -
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Auth | Argon2 passwords, JWT (HS256), rotating refresh tokens |
| Database | PostgreSQL 15 with Row-Level Security |
| Queue | Redis 7 + ARQ |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, TanStack Query |
| Drag & Drop | @dnd-kit (Kanban pipeline) |
| Forms | React Hook Form + Zod |
| Reverse Proxy | Caddy 2 (auto-HTTPS) |
| Containers | Docker Compose |
| CI/CD | GitHub Actions |

---

## Security

- HTTPS enforced via Caddy + HSTS headers
- Argon2id password hashing
- **httpOnly cookies** for both access (15 min) and refresh (30 days, rotating) JWTs — no tokens in `localStorage`, no XSS exfiltration
- Optional TOTP 2FA with hashed single-use backup codes
- Per-route rate limiting via slowapi + Redis (login, register, refresh, forgot/reset password, 2FA verify, public lead form)
- **PostgreSQL Row-Level Security** with `FORCE ROW LEVEL SECURITY` on every tenant-scoped table; every authenticated request sets `app.current_tenant`
- **Webhook signature verification**: Stripe (`stripe.Webhook.construct_event`), Twilio (HMAC-SHA1 of url + sorted form fields), Resend / Svix (HMAC-SHA256 with replay window)
- **Atomic per-tenant quote/invoice numbering** via a SQL function using `UPDATE ... RETURNING`; unique `(tenant_id, number)` constraints
- **Boot-time safety guard**: the API refuses to start in `production` if `JWT_SECRET` / `JWT_REFRESH_SECRET` are placeholders or < 32 chars, if the DB is SQLite, if `ALLOWED_ORIGINS` is missing, or if a provider is enabled without its webhook secret
- Audit log for: login, password change, member changes, billing, GDPR actions
- GDPR: data export job (per-tenant JSON dump emailed to owner), right-to-erasure job (PII redacted, audit preserved), consent tracking

---

## License

Proprietary — all rights reserved.
