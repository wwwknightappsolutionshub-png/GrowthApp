# CRM Enterprise — Phase 3 API

Branch: `feature/crm-enterprise`  
Base path: `/api/v1/crm`

## Pipelines & board

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipelines` | List pipelines + stages |
| POST | `/pipelines` | Create pipeline (seeds default stages) |
| PATCH | `/pipelines/{id}` | Update pipeline |
| DELETE | `/pipelines/{id}` | Soft-deactivate pipeline |
| POST | `/pipelines/{id}/stages` | Add stage |
| PATCH | `/stages/{id}` | Update stage |
| POST | `/pipelines/{id}/stages/reorder` | Reorder stages |
| GET | `/board?pipeline_id=` | **Unified kanban** (leads + deals) |
| POST | `/board/move` | Move lead or deal card |
| POST | `/deals/{id}/move-stage` | Move deal by `stage_id` or legacy `stage` name |

Legacy: `GET /pipeline`, `POST /deals/{id}/move` (deals only, stage string).

## Customers, activities, tags

| Method | Path |
|--------|------|
| GET/POST/PATCH/DELETE | `/customers` (existing) |
| GET | `/customers/{id}/bookings` (read-only) |
| GET/POST | `/activities?entity_type=&entity_id=` |
| GET/POST | `/tags`, `/tags/assign`, `/tags/entity` |

## Custom fields, filters, scoring

| Method | Path |
|--------|------|
| GET/POST | `/custom-fields`, `PUT /custom-fields/values` |
| GET/POST/DELETE | `/filters` |
| GET/POST | `/score-rules` |
| POST | `/leads/{id}/apply-scores` |
| POST | `/leads/{id}/enrich` (AI summary) |

## Bulk, merge, dashboard, import

| Method | Path |
|--------|------|
| POST | `/bulk` |
| POST | `/duplicates/scan` |
| POST | `/merge` |
| GET | `/dashboard` |
| GET | `/export/leads` |
| POST | `/import/leads` |
| GET/POST | `/attachments` |
| POST | `/assignments` |

## RBAC permissions (new)

`crm.import`, `crm.export`, `crm.merge`, `crm.bulk`, `crm.settings`, `crm.assign`

## Automation events (new)

`lead_stage_changed`, `deal_stage_changed` (plus existing `lead_created`, `job_completed`).
