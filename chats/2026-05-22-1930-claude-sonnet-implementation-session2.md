# Session: Implementation Session 2 — All 8 Core API Modules

**Date:** 2026-05-22  
**Agent:** claude-sonnet-4-6 (session 2, after context compaction)  
**Tasks:** L118–L126 (all 8 core API modules), workflow doc clarification

## Objective

Complete implementation of all 8 core API modules after context compaction from session 1, then document the one-command-per-call rule for bootstrap scripts.

## Tasks Completed

- **todo:L118** — `projects` module: CRUD routes, service, serialization, optimistic locking, slug conflict handling.
- **todo:L119** — `project_sections` module: nested CRUD under `/api/projects/{id}/sections`, sort_order support.
- **todo:L120** — `project_status` module: nested routes, optional `project_section_id` (null = project-wide).
- **todo:L121** — `tasks` module: list/create, get/patch/claim/heartbeat/complete/block; atomic lease via targeted UPDATE + rowcount check; `LeaseConflictError` / `LeaseOwnershipError` → 409.
- **todo:L122** — `agents` module: standard CRUD, name uniqueness via IntegrityError → 409.
- **todo:L123** — skipped (Go CLI scaffold — separate task).
- **todo:L124** — `runs` module: heartbeat/complete/fail via targeted UPDATE, atomic state transitions.
- **todo:L125** — `events` module: append-only, GET project events / POST global, no update/delete.
- **todo:L126** — `reviews` module: findings, status updates via PATCH with version check.
- **Workflow doc** — Added "Bootstrap Script Rules" section to `AGENT_WORKFLOW.md` and "One command per call" note to `docs/Bootstrap-CLI.md`.

## Key Decisions

- Atomic task lease: SQLAlchemy `update()` with WHERE on `status`, `claimed_until`, and `claimed_by`; `rowcount == 0` → 409. No SELECT FOR UPDATE needed.
- Events table is append-only by design; no `updated_at` field.
- `project_section_id = null` means project-wide/general scope for both status records and tasks.

## Claude Code Permission Finding

`Bash(./scripts/*)` glob matches the full command string. Compound `&&` commands don't match because the second command after `&&` is not `./scripts/*`. Fix: each bootstrap script must be its own separate tool invocation.

## Validation

`make lint` clean, `make validate` passes (imports OK).

## Commits

- `28b4c25` feat(api): implement projects module
- `44dd056` feat(api): implement project_sections module
- `d3cac9c` feat(api): implement project_status module
- `d695644` feat(api): implement tasks module with atomic lease coordination
- `c1867ad` feat(api): implement agents, runs, events, and reviews modules
- `0676cfa` docs: update MEMORY, status, and TODO
- `25d31ba` docs(workflow): clarify one-command-per-call rule

## Next Steps

1. Generate and run first Alembic migration (`make db-up` + `make migrate`). **→ Done in session 3.**
2. Configure pytest with PostgreSQL fixture cleanup (todo:L104). **→ Done in session 3.**
3. Add curl smoke checks for health and basic workflow (todo:L105). **→ Done in session 3.**
4. API contract tests for core modules.
5. Go CLI scaffold (todo:L110/L123).
