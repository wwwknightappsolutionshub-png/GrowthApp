# CRM Enterprise — Phase 2: Database Migration Plan

**Branch:** `feature/crm-enterprise`  
**Revision:** `028_crm_enterprise` (revises `027_tenant_business_site`)  
**Status:** Implemented — migration `028_crm_enterprise` on branch `feature/crm-enterprise`.

## Approved product decisions (Phase 1)

| Decision | Choice |
|----------|--------|
| Pipelines | **Multiple** per tenant |
| Kanban | **Leads + deals** on one board |
| Contact label | **Customers** (table `customers`) |
| Exclusions list | Ignored — implement allowed scope only |

---

## Design principles

1. **Additive only** — no column drops; legacy `deals.stage` string kept until Phase 3 backfill completes.
2. **Reuse** — `leads`, `customers`, `deals`, `tasks`, `deal_activities`, `customer_segments`, `messages`.
3. **Postgres RLS** — every new tenant table gets `tenant_isolation` policy (GUC `app.current_tenant`).
4. **SQLite dev** — tables created; RLS skipped when dialect ≠ postgresql (same as `003`, `005`).

---

## Unified kanban model

One API returns columns from `crm_stages`; cards are either:

| Card type | Source table | Position field |
|-----------|--------------|----------------|
| `lead` | `leads` | `stage_order` |
| `deal` | `deals` | `stage_order` |

Both reference:

- `pipeline_id` → `crm_pipelines.id`
- `stage_id` → `crm_stages.id`

**Pipeline rules**

- Tenant may have N pipelines (`crm_pipelines`).
- Exactly one `is_default = true` per tenant (partial unique index).
- Stages ordered by `position` (0..n).
- Optional `applies_to`: `leads` | `deals` | `both` (default `both` for unified board).

**Data migration (in upgrade)**

For each tenant with existing deals:

1. Insert default pipeline `"Sales"` (`is_default=true`).
2. Insert stages matching legacy `STAGES`: New, Contacted, Quoted, Booked, Completed, Lost.
3. Set `deals.pipeline_id`, `deals.stage_id` from `deals.stage` name match.
4. Set `leads.pipeline_id` to default pipeline; `leads.stage_id` = first stage (New); `leads.stage_order` from `created_at` ordering.

---

## New tables

### `crm_pipelines`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK tenants | indexed |
| name | varchar(100) | |
| description | text | nullable |
| is_default | boolean | default false |
| is_active | boolean | default true |
| created_at / updated_at | timestamptz | |

**Indexes:** `(tenant_id)`, unique `(tenant_id) WHERE is_default` (postgres).

### `crm_stages`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | denormalized for RLS |
| pipeline_id | UUID FK crm_pipelines CASCADE | |
| name | varchar(80) | |
| position | int | kanban order |
| color | varchar(20) | UI hex/token |
| applies_to | varchar(10) | `both` default |
| automation_event | varchar(80) | nullable; fire on enter |
| is_won | boolean | default false |
| is_lost | boolean | default false |
| created_at | timestamptz | |

**Indexes:** `(pipeline_id, position)`, `(tenant_id, pipeline_id)`.

### `crm_assignments`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| entity_type | varchar(20) | `lead`, `deal`, `customer` |
| entity_id | UUID | no polymorphic FK (app-enforced) |
| user_id | UUID FK users | |
| role | varchar(30) | `owner`, `collaborator` |
| created_at | timestamptz | |

**Indexes:** `(tenant_id, entity_type, entity_id)`, `(user_id)`.

### `crm_custom_field_definitions`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| entity_type | varchar(20) | `customer`, `lead`, `deal` |
| field_key | varchar(64) | slug |
| label | varchar(120) | |
| field_type | varchar(20) | text, number, date, boolean, select |
| options | jsonb | select choices |
| is_required | boolean | |
| position | int | |
| created_at | timestamptz | |

**Unique:** `(tenant_id, entity_type, field_key)`.

### `crm_custom_field_values`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| definition_id | UUID FK definitions CASCADE | |
| entity_type | varchar(20) | |
| entity_id | UUID | |
| value_text | text | nullable |
| value_number | numeric | nullable |
| value_bool | boolean | nullable |
| value_date | timestamptz | nullable |
| value_json | jsonb | nullable |
| updated_at | timestamptz | |

**Unique:** `(definition_id, entity_id)`.

### `crm_tags` + `crm_tag_assignments`

**`crm_tags`:** `id`, `tenant_id`, `name`, `color`, `created_at` — unique `(tenant_id, name)`.

**`crm_tag_assignments`:** `id`, `tenant_id`, `tag_id`, `entity_type`, `entity_id` — unique `(tag_id, entity_type, entity_id)`.

### `crm_attachments`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| entity_type | varchar(20) | lead, deal, customer, task |
| entity_id | UUID | |
| uploaded_by_user_id | UUID FK | nullable |
| file_name | varchar(255) | |
| mime_type | varchar(100) | |
| size_bytes | int | |
| storage_path | text | local/S3 path |
| created_at | timestamptz | |

### `crm_activities`

Unified timeline (denormalized feed).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| entity_type | varchar(20) | lead, deal, customer |
| entity_id | UUID | |
| activity_type | varchar(50) | note, stage_changed, email, task, call, merge, … |
| title | varchar(255) | nullable |
| body | text | nullable |
| user_id | UUID FK | nullable |
| metadata | jsonb | |
| created_at | timestamptz | indexed |

**Indexes:** `(tenant_id, entity_type, entity_id, created_at DESC)`.

*Phase 3 services write here; optional sync from `deal_activities` on upgrade.*

### `crm_saved_filters`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| user_id | UUID FK | nullable = shared |
| name | varchar(100) | |
| entity_type | varchar(20) | lead, deal, customer |
| rules | jsonb | query DSL (align with segments) |
| is_default | boolean | |
| created_at | timestamptz | |

### `crm_score_rules`

Rule-based lead scoring (complements AI `leads.score`).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| name | varchar(100) | |
| priority | int | lower = first |
| conditions | jsonb | field/op/value |
| points | int | |
| is_active | boolean | |
| created_at | timestamptz | |

### `crm_import_jobs`

CSV import/export tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| user_id | UUID FK | |
| job_type | varchar(20) | import, export |
| entity_type | varchar(20) | lead, customer |
| status | varchar(20) | pending, running, done, failed |
| file_path | text | |
| row_count | int | |
| error_log | text | |
| created_at / completed_at | timestamptz | |

### `crm_duplicate_candidates` (merge workflow)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| entity_type | varchar(20) | customer, lead |
| primary_id | UUID | |
| duplicate_id | UUID | |
| match_score | numeric | |
| status | varchar(20) | pending, merged, dismissed |
| created_at | timestamptz | |

---

## Alter existing tables

### `leads`

| Add column | Type | Nullable |
|------------|------|----------|
| pipeline_id | UUID FK crm_pipelines | yes → backfill |
| stage_id | UUID FK crm_stages | yes |
| stage_order | int | default 0 |
| assigned_user_id | UUID FK users | yes |

**Indexes:** `(tenant_id, pipeline_id, stage_id)`, `(tenant_id, stage_id, stage_order)`.

### `deals`

| Add column | Type | Notes |
|------------|------|-------|
| pipeline_id | UUID FK | |
| stage_id | UUID FK | |
| Keep `stage` | varchar | legacy; synced in Phase 3 on move |

**Indexes:** same pattern as leads.

### `customers`

| Add column | Type | Notes |
|------------|------|-------|
| assigned_user_id | UUID FK users | nullable |

(`tags` via `crm_tag_assignments`; profile fields stay on row.)

### `tasks`

No schema change required (`due_at`, `reminder_at` exist). Phase 4 adds views only.

### `customer_segments`

| Add column | Type | Notes |
|------------|------|-------|
| entity_type | varchar(20) | default `customer`; allow `lead` |

---

## RLS (PostgreSQL only)

Apply to all new tables:

```sql
ALTER TABLE "<table>" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "<table>" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "<table>"
  USING (current_setting('app.current_tenant', true) = ''
      OR current_setting('app.current_tenant', true) IS NULL
      OR tenant_id::text = current_setting('app.current_tenant', true))
  WITH CHECK (... same ...);
```

**Tables:** `crm_pipelines`, `crm_stages`, `crm_assignments`, `crm_custom_field_definitions`, `crm_custom_field_values`, `crm_tags`, `crm_tag_assignments`, `crm_attachments`, `crm_activities`, `crm_saved_filters`, `crm_score_rules`, `crm_import_jobs`, `crm_duplicate_candidates`.

---

## Backfill script (inside `upgrade()`)

```
FOR each tenant_id IN tenants:
  CREATE pipeline "Sales" (is_default=true)
  CREATE stages [New, Contacted, Quoted, Booked, Completed, Lost]
  UPDATE deals SET pipeline_id, stage_id FROM deals.stage
  UPDATE leads SET pipeline_id, stage_id=(New), stage_order=row_number
```

**Lost/Won flags:** `Completed` → `is_won=true`, `Lost` → `is_lost=true`.

---

## Breaking change assessment

| Area | Risk | Mitigation |
|------|------|------------|
| `GET /crm/pipeline` | Response shape changes | Phase 3: new `/crm/board` + keep old endpoint 1 release |
| `deals.stage` | Still populated on move | Dual-write in service |
| Empty pipelines | New tenants | Seed on tenant create hook + migration backfill |

**No breaking DB changes** for existing rows (nullable FKs until backfill).

---

## File deliverables (Phase 2 implementation)

| File | Action |
|------|--------|
| `alembic/versions/028_crm_enterprise.py` | New migration |
| `app/modules/crm/models.py` | New SQLAlchemy models |
| `app/modules/crm/pipeline_models.py` | Optional split |
| `app/modules/leads/models.py` | Add FK columns |

---

## Phase 2 approval checklist

- [ ] Approve table list
- [ ] Approve unified board FK model
- [ ] Approve legacy `deals.stage` dual-write approach
- [ ] Approve default pipeline name "Sales" + 6 legacy stages

**Phase 2 complete.** Next: **Approve Phase 3** (backend API routes).

### VPS apply

```bash
cd /www/wwwroot/customerflow/apps/api
git pull origin feature/crm-enterprise
.venv/bin/alembic upgrade head
sudo systemctl restart customerflow-api customerflow-worker
```
