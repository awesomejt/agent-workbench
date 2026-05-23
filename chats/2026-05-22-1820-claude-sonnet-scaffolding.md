# Session: Flask API Scaffolding

**Date:** 2026-05-22  
**Agent:** claude-sonnet-4-6  
**Objective:** Advance from planning phase into scaffolding — decide Flask package layout, scaffold the API backend, Docker Compose, Alembic, and monorepo structure.

---

## Tasks Completed

| Task ID | Title | Notes |
|---------|-------|-------|
| todo:L59 | Decide Flask package layout | `src/` layout, app factory, Flask-SQLAlchemy, pydantic-settings |
| todo:L60 | Define initial module boundaries | 8 modules scaffolded with models + blueprint stubs |
| todo:L86 | Evaluate pydantic-settings | Adopted in `api/src/agent_workbench/config.py` |
| todo:L90 | Add example env files | `api/.env.example` |
| todo:L95 | Add backend project structure | `api/src/agent_workbench/` full scaffold |
| todo:L96 | Add Docker Compose with PostgreSQL 18 | `docker-compose.yml` with db, api (profile), migrations (profile) |
| todo:L97 | Add Docker Compose secret/env-file pattern | Documented in `.env.example` and Makefile |
| todo:L98 | Add example env files without secrets | `api/.env.example` |
| todo:L99 | Add Alembic migration tooling | `api/alembic.ini`, `api/migrations/env.py`, `api/migrations/script.py.mako` |
| todo:L100 | Add migration commands requiring explicit APP_ENV | `make migrate-dev/stage/prod` in Makefile |
| todo:L103 | Expand root Makefile | Full rewrite: setup, db-up/down, migrate, lint, format, type-check, validate, test, smoke, build-cli, clean |
| (new) | Establish api/cli/web top-level dirs | `cli/.gitkeep`, `web/.gitkeep`; Python in `api/` |

---

## Key Decisions Made

### Flask Package Layout
- `src/` layout inside `api/` (clean imports, no accidental package discovery)
- Application factory: `create_app()` in `api/src/agent_workbench/app.py`
- Flask-SQLAlchemy 3.x (wraps SQLAlchemy 2.x, handles Flask context integration)
- pydantic-settings for typed config — `DATABASE_URL` is required, fails fast if not set
- Direct Alembic (not flask-migrate wrapper) for full control
- Per-module Blueprints matching the architecture: projects, project_sections, project_status, tasks, agents, runs, events, reviews

### Repository Monorepo Structure (Jason's direction, 2026-05-22)
```
api/        Python/Flask API
cli/        Go CLI stub (.gitkeep)
web/        React web UI stub (.gitkeep, post-MVP)
scripts/    Bootstrap agent scripts (root, interim tools)
db/         Database bootstrap SQL (root)
docker-compose.yml   Orchestrates all services (root)
Makefile             Wraps all component targets (root)
```

### Database / Schema
- `agent_workbench` schema in PostgreSQL (same name across all envs, separate servers/databases per env)
- Alembic `env.py` reads `APP_ENV` → resolves `AGENT_WORKBENCH_{ENV}_DATABASE_URL` or `DATABASE_URL`
- Creates schema and pgcrypto extension on first migration run
- `alembic_version` table lives in `agent_workbench` schema

### Docker Compose Workflow (Jason's preference)
- Docker Compose for service operations (db, api, migrations)
- Profiles: `--profile api` for API server, `--profile migrate` for migration runs
- Dev tools (lint, test, type-check) still run via `cd api && uv run` — no Docker overhead needed there
- `make db-up` starts db; `make migrate` runs migrations via Docker Compose

### Version Policy (Jason's preference)
- Target major.minor only (e.g., `flask>=3.1`, `sqlalchemy>=2.0`)
- Patch versions managed automatically by uv/go modules/npm
- CachyOS rolling distro keeps packages current naturally

### Bootstrap Scripts
- `scripts/task-claim`, `scripts/task-complete`, etc. are intentional interim tools until Go CLI is ready
- Use them throughout sessions for task tracking — more deterministic than AI state management
- They track local state in `.agent-workbench/bootstrap-state.json` (git-ignored)

---

## Files Created / Modified

### New: api/ directory (full tree)
```
api/
  .env.example
  Dockerfile
  alembic.ini
  pyproject.toml
  uv.lock
  migrations/
    env.py
    script.py.mako
    versions/.gitkeep
  src/
    agent_workbench/
      __init__.py
      app.py           # create_app() factory
      config.py        # Settings(BaseSettings), DATABASE_URL required
      database.py      # db = SQLAlchemy(model_class=Base), SCHEMA="agent_workbench"
      errors.py        # register_error_handlers()
      agents/          # models.py, routes.py, service.py
      events/          # models.py (append-only), routes.py, service.py
      project_sections/ # models.py, routes.py, service.py
      project_status/  # models.py, routes.py, service.py
      projects/        # models.py, routes.py, service.py
      reviews/         # models.py, routes.py, service.py
      runs/            # models.py, routes.py, service.py
      tasks/           # models.py (has lease fields), routes.py, service.py
```

### New: cli/.gitkeep, web/.gitkeep
### New: docker-compose.yml (root)
### Modified: Makefile (full rewrite, API_DIR=api prefix)
### Modified: docs/Tech-Stack.md (added structure section, Docker Compose workflow, version policy)
### Modified: MEMORY.md (added scaffolding decisions section, run log entry)
### Modified: TODO.md (marked ~10 tasks complete)
### Modified: status.yaml (active, phase: scaffolding)

---

## SQLAlchemy Models Summary

All models use:
- `Uuid(as_uuid=True)` primary keys with `default=uuid.uuid4`
- `DateTime(timezone=True)` for all timestamps
- `version: int` for optimistic locking on mutable tables
- `MetaData(schema="agent_workbench")` on Base → all tables auto-prefixed

| Model | Table | Notable fields |
|-------|-------|----------------|
| Project | projects | slug (unique), project_type, git_remote_url, local_path, default_agent, metadata |
| ProjectSection | project_sections | project_id FK, slug, section_type, sort_order, metadata |
| ProjectStatus | project_statuses | project_id FK, project_section_id FK (nullable), status, phase, summary, reason |
| Task | tasks | project_id FK, project_section_id FK (nullable), status, priority, phase, assignee_type/name, claimed_by, claimed_until, lease_version, idempotency_key |
| Agent | agents | name (unique), agent_type, capabilities (JSON), default_model |
| Run | runs | project_id FK, task_id FK (nullable), agent_name, status, heartbeat fields |
| Event | events | project/task/run FKs (all nullable), event_type, actor_type/name, payload (JSON) — append-only |
| Review | reviews | project_id FK, source, severity, status, finding, linked_task_id FK (nullable) |

---

## Validation Results

```
make validate  → python3 -m py_compile scripts/awb.py: OK
               → imports ok (create_app, all 8 modules imported)
make lint      → ruff check src/: All checks passed!
```

Installed package versions (informational): Flask 3.1, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0, Alembic 1.18, psycopg 3.3, pydantic-settings 2.14, Python 3.14.5.

---

## Open State / Next Steps

**Bootstrap script state:** `todo:L59` marked complete; other scaffolding tasks marked done directly in TODO.md.

**Next task from bootstrap:** `todo:L61` — "Define initial API route style and compatibility policy without URL versioning by default." (largely documented in `docs/API-Contracts.md` already — quick close)

**Highest value next work:**
1. Close out remaining Discovery/Planning definition tasks quickly (L61-L69) — most are already documented
2. Implement `projects` module CRUD routes (first Implementation Phase task, unlocks testing the system end-to-end)
3. Add pytest configuration with PostgreSQL fixture cleanup (L104)

**Blockers (none blocking scaffolding):**
- Jason still needs to confirm dev/stage/prod database names/users before `make migrate-dev/stage/prod` is usable
- That blocker is tracked in TODO.md "Needs Attention" and MEMORY.md

---

## Commit

`e75cb7f feat(scaffold): add Flask API package, Docker Compose, Alembic, and monorepo structure`  
53 files changed, 1695 insertions, 47 deletions
