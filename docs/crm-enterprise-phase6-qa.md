# CRM Enterprise — Phase 6: QA

Branch: `feature/crm-enterprise`  
Automated: `apps/api/tests/test_crm_enterprise.py`, `test_crm_enterprise_integration.py`

## Scope (in)

| Area | Verified |
|------|----------|
| Default pipeline + 6 stages | Integration test |
| Unified board (leads + deals) | HTTP smoke + manual |
| Stage move → activity + automation enqueue | Integration test (`entity_type=lead` on lead moves) |
| Unified timeline (notes, messages, automations) | Integration test |
| Customer / deal / lead bookings (read-only) | Integration tests |
| RBAC on enterprise routes | HTTP 401 without auth |
| UI routes (Phase 4) | Manual checklist below |

## Out of scope (not in this upgrade)

- Replacing legacy `/dashboard/leads` or `/dashboard/tasks` UIs
- New email/SMS send paths (uses existing messaging workers)
- Writing or rescheduling bookings from CRM
- Prisma/Clerk/tRPC (stack is FastAPI + SQLAlchemy + Next.js)
- Full automation step execution in tests (enqueue is mocked)

## Automated test run

```bash
cd apps/api
python -m pytest tests/test_crm_enterprise.py tests/test_crm_enterprise_integration.py -q
```

## Manual UI checklist

### Pipeline board (`/dashboard/crm/board`)

- [ ] Select pipeline; columns show leads and deals
- [ ] Drag lead to another stage; card stays in new column after refresh
- [ ] Click card → panel opens with timeline, bookings, enrich (lead)
- [ ] AI enrich on lead adds `ai_enrichment` row on timeline

### Customers (`/dashboard/crm/customers`)

- [ ] List loads; open profile
- [ ] Add note → appears on timeline
- [ ] Customer with booking → appointments card populated (read-only)
- [ ] Link to automations works

### Settings (`/dashboard/crm/settings`)

- [ ] Create pipeline; appears in board selector
- [ ] Integrations card visible

### Automations (`/dashboard/automations`)

- [ ] Triggers show “Lead moved on CRM pipeline” / “Deal moved on CRM pipeline”
- [ ] Active automation on `lead_stage_changed` runs after board move (worker + Redis required)

### Messaging integration

- [ ] Send email to customer (existing inbox/outreach)
- [ ] Same customer timeline shows outbound email entry

### Segments & import

- [ ] `/dashboard/crm/segments` loads
- [ ] `/dashboard/crm/import` export CSV; import CSV creates leads in first stage

### Dashboard (`/dashboard/crm/dashboard`)

- [ ] Widgets show counts without error

## Regression

- [ ] Legacy `GET /crm/pipeline` still works (deals-only view)
- [ ] Tenant isolation: user A cannot read tenant B CRM data (RLS on PostgreSQL)

## Bugs fixed in Phase 6

- **Lead stage automation**: `trigger_automation_for_event` now passes `entity_type="lead"` so runs match lead automations (was defaulting to `deal`).
- **`GET /crm/timeline`**: Route registered on enterprise router (was missing → 404).
- **Bookings payload**: `service_type` in API response uses `service_description` when the column is absent on `Booking`.

## Sign-off

| Role | Date | Notes |
|------|------|-------|
| Dev | | Automated tests green |
| QA | | Manual checklist complete |
