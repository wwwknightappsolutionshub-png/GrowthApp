# CRM Enterprise — Phase 4 UI

Branch: `feature/crm-enterprise`

## Routes

| Path | Screen |
|------|--------|
| `/dashboard/crm` | Redirects → `/dashboard/crm/board` |
| `/dashboard/crm/dashboard` | Widgets (new leads, pipeline value, breakdowns) |
| `/dashboard/crm/board` | **Unified kanban** (leads + deals), pipeline selector |
| `/dashboard/crm/customers` | Customer list |
| `/dashboard/crm/customers/[id]` | Profile, notes, bookings (read-only) |
| `/dashboard/crm/segments` | Segment builder (existing API) |
| `/dashboard/crm/import` | CSV import/export leads |
| `/dashboard/crm/settings` | Pipelines + custom fields |

Tasks remain at `/dashboard/tasks` (existing kanban).

## Components

- `components/crm/CrmSubNav.tsx`
- `components/crm/UnifiedPipelineBoard.tsx`
- `components/crm/CustomersList.tsx`

## API client

Extended `crm` object in `lib/api-client.ts` with all Phase 3 endpoints.
