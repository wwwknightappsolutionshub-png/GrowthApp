# Business site (subdomain + QR)

## Tenant experience

1. Complete onboarding → redirected to **Dashboard → Business Page** (`/dashboard/site-builder`).
2. Pick an enterprise template (matched to business category).
3. Edit in the landing page editor (sections, CTAs, `lead_form`).
4. **Publish** → live at `https://{tenant-slug}.customerflowai.online` + QR emailed + downloadable PNG.

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/tenants/me/business-site` |
| POST | `/api/v1/tenants/me/business-site/bootstrap?template_slug=` |
| POST | `/api/v1/tenants/me/business-site/publish` |
| GET | `/api/v1/tenants/me/business-site/qr.png` |
| GET | `/api/v1/public/site/{tenant_slug}` |

## VPS / DNS (required for subdomains)

1. **DNS:** wildcard `*.customerflowai.online` → VPS IP.
2. **TLS:** certificate must cover `*.customerflowai.online` (Caddy `tls { dns ... }` or aaPanel wildcard).
3. **Reverse proxy:** route `*.customerflowai.online` to `customerflow-web` (same Next.js app).
4. **Env:** `BUSINESS_SITE_BASE_DOMAIN=customerflowai.online` on API; `BUSINESS_SITE_BASE_DOMAIN` on web build if using middleware rewrite.

Next.js middleware rewrites subdomain hosts to `/sites/{slug}`.

## Migration

`027_tenant_business_site` — `primary_landing_page_id`, `business_site_published`, `business_site_published_at`.
