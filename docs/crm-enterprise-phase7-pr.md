# CRM Enterprise — Phase 7: Pull request

## Status

- **Branch pushed:** `origin/feature/crm-enterprise` (commit `4e6d2bc` + Phases 2–4 below)
- **Open PR:** https://github.com/wwwknightappsolutionshub-png/GrowthApp/compare/main...feature/crm-enterprise?expand=1

## Target

- **Base:** `main`
- **Head:** `feature/crm-enterprise`

## PR title (suggested)

`feat(crm): Enterprise CRM — pipelines, unified board, integrations`

## PR body (paste into GitHub)

```markdown
## Summary

- **CRM Enterprise** (Phases 1–7): multiple pipelines, unified leads+deals kanban, customers hub, tags/activities/custom fields, bulk/merge/import, dashboard, and integrations with automations, messaging timeline, read-only bookings, and AI lead enrich.
- **Migrations:** `026_enterprise_booking`, `027_tenant_business_site`, `028_crm_enterprise` (run `alembic upgrade head`).
- **Also on branch:** enterprise booking module, collapsible sidebar TS fix (parent history).

## Test plan

- [ ] `cd apps/api && python -m pytest tests/test_crm_enterprise.py tests/test_crm_enterprise_integration.py -q`
- [ ] `alembic upgrade head` on staging DB
- [ ] Redeploy API + ARQ worker; rebuild web
- [ ] Manual checklist: `docs/crm-enterprise-phase6-qa.md`
- [ ] Smoke `/dashboard/crm/board` (drag card, open panel, enrich lead)

## Docs

- `docs/crm-enterprise-notes.md` (overview)
- Phase docs: `crm-enterprise-phase2-migration.md` through `phase7-pr.md`
```

## Pre-merge checklist

- [ ] CI green on PR
- [ ] `alembic upgrade head` on staging (026 → 027 → 028 if not applied)
- [ ] API + ARQ worker redeployed
- [ ] Web rebuild (`npm run build`)
- [ ] Manual smoke: `crm-enterprise-phase6-qa.md`

## Merge notes

This branch includes **enterprise booking** migrations (`026`, `027`) from its parent history. If `main` already has booking elsewhere, resolve migration chain before merge.

CRM-only commits (for reference):

- `50a7b3a` Phase 2 migration  
- `8b214d7` Phase 3 API  
- `ff25782` Phase 4 UI  
- (Phases 5–7 in final commit on branch)

## After merge

1. Delete `feature/crm-enterprise` when done  
2. Run QA checklist on production/staging tenant  
3. Announce: new `/dashboard/crm/board` replaces monolithic CRM entry  
