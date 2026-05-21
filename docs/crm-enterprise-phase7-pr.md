# CRM Enterprise — Phase 7: Pull request

## Target

- **Base:** `main`
- **Head:** `feature/crm-enterprise`

## PR title (suggested)

`feat(crm): Enterprise CRM — pipelines, unified board, integrations`

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
