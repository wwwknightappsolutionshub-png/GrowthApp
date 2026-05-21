# CRM Enterprise Upgrade — Implementation Notes

**Branch:** `feature/crm-enterprise`  
**Migration:** `028_crm_enterprise` (requires `027_tenant_business_site` → `026_enterprise_booking` on `main`)  
**API prefix:** `/api/v1/crm`

> This branch also contains enterprise booking (`026`/`027`) and the sidebar TypeScript fix (`6f50639`) from its parent line. Merge order: land booking migrations first, or merge this branch as one unit.

---

## Phases delivered

| Phase | Deliverable | Doc |
|-------|-------------|-----|
| 1 | Architecture + product decisions (multi-pipeline, unified board, Customers label) | This file |
| 2 | Alembic `028`, pipeline/stage/CRM tables, default Sales pipeline | `crm-enterprise-phase2-migration.md` |
| 3 | Enterprise API (board, bulk, merge, scoring, import/export) | `crm-enterprise-phase3-api.md` |
| 4 | Next.js routes: dashboard, board, customers, segments, import, settings | `crm-enterprise-phase4-ui.md` |
| 5 | Integrations: automations, messaging timeline, bookings read-only, AI enrich | `crm-enterprise-phase5-integration.md` |
| 6 | Integration tests + manual QA checklist | `crm-enterprise-phase6-qa.md` |
| 7 | Release notes + PR to `main` | This file |

---

## Product decisions (approved)

- **Multiple pipelines** per tenant  
- **Unified kanban**: leads + deals on one board  
- **UI label**: Customers (`customers` table)  
- **Exclusions** from original prompt: ignored — scope as implemented  

---

## Key capabilities

### Pipelines & board

- Default pipeline **Sales**: New → Contacted → Quoted → Booked → Completed → Lost  
- `GET /crm/board`, `POST /crm/board/move`  
- Stage moves enqueue `lead_stage_changed` / `deal_stage_changed` (with `entity_type=lead` for leads)

### Enterprise CRM data

Tags, activities, custom fields, saved filters, score rules, attachments, assignments, duplicate scan/merge, dashboard widgets, CSV import/export.

### Integrations (Phase 5)

| System | Behaviour |
|--------|-----------|
| **Automations** | Stage-change events; runs appear on `GET /crm/timeline` |
| **Messaging** | Emails/SMS on conversations matched by customer/deal/lead email |
| **Bookings** | Read-only lists on customer, deal (via customer), lead (email match) |
| **AI** | `POST /crm/leads/{id}/enrich` → summary + timeline entry |

### RBAC (new permissions)

`crm.import`, `crm.export`, `crm.merge`, `crm.bulk`, `crm.settings`, `crm.assign`

---

## Web routes

| Path | Purpose |
|------|---------|
| `/dashboard/crm` | → `/dashboard/crm/board` |
| `/dashboard/crm/dashboard` | Metrics |
| `/dashboard/crm/board` | Unified kanban + card panel |
| `/dashboard/crm/customers` | List |
| `/dashboard/crm/customers/[id]` | Profile + unified timeline |
| `/dashboard/crm/segments` | Segments |
| `/dashboard/crm/import` | CSV |
| `/dashboard/crm/settings` | Pipelines, fields, integrations |

---

## Deploy / migrate

```bash
cd apps/api
alembic upgrade head   # applies 026 → 027 → 028 when not yet on DB
```

Restart API + worker (automation enqueue). Rebuild web:

```bash
cd apps/web
npm run build
```

---

## Tests

```bash
cd apps/api
python -m pytest tests/test_crm_enterprise.py tests/test_crm_enterprise_integration.py -q
```

---

## Post-merge manual smoke

See checklist in `crm-enterprise-phase6-qa.md` (board drag, timeline, enrich, automations labels).

---

## Files (high signal)

| Area | Path |
|------|------|
| Migration | `apps/api/alembic/versions/028_crm_enterprise.py` |
| Models | `apps/api/app/modules/crm/pipeline_models.py` |
| Board service | `apps/api/app/modules/crm/pipeline_service.py` |
| Enterprise API | `apps/api/app/modules/crm/enterprise_router.py`, `enterprise_service.py` |
| UI board | `apps/web/components/crm/UnifiedPipelineBoard.tsx`, `CrmBoardCardPanel.tsx` |
| Timeline | `apps/web/components/crm/CrmEntityTimeline.tsx` |
