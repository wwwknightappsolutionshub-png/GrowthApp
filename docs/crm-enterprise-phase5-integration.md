# CRM Enterprise — Phase 5: Integration layer

Phase 5 wires CRM to existing platform modules without new infrastructure.

## Automations

- Pipeline moves enqueue `lead_stage_changed` and `deal_stage_changed` (see `pipeline_service.py`).
- Automations UI lists these triggers; CRM Settings documents the link.
- Timeline shows `automation_run` entries for the entity.

## Bookings (read-only)

| Entity   | Endpoint                              | Resolution                          |
|----------|---------------------------------------|-------------------------------------|
| Customer | `GET /crm/customers/{id}/bookings`    | `bookings.customer_id`              |
| Deal     | `GET /crm/deals/{id}/bookings`        | Via deal’s `customer_id`            |
| Lead     | `GET /crm/leads/{id}/bookings`        | Customer matched by lead email      |

Shown on customer profile, pipeline board card panel, and deal/lead panels.

## Messaging / email

- `GET /crm/timeline?entity_type=&entity_id=` merges:
  - `crm_activities`
  - `messages` from conversations (customer_id, deal_id, or email/phone match for leads)
  - `automation_runs`

No duplicate send path — uses existing `messages` + worker delivery.

## AI enrichment

- `POST /crm/leads/{id}/enrich` (existing) logs `ai_enrichment` on timeline.
- Board card panel exposes **AI enrich** and **Apply scores**.

## Frontend

- `CrmEntityTimeline` — unified timeline component
- `CrmBoardCardPanel` — slide-over on pipeline board
- Customer profile uses timeline API
- CRM Settings → Integrations card

## Phase 6

See `crm-enterprise-phase6-qa.md` for automated tests and the manual UI checklist.
