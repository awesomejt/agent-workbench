# Session: Migration, Pytest Fixtures, Smoke Checks

**Date:** 2026-05-22  
**Agent:** claude-sonnet-4-6 (session 3)  
**Tasks:** First Alembic migration, pytest autouse fixtures, curl smoke checks

## Objective

Pick up from session 2. Run first Alembic migration against local DB, configure pytest with real PostgreSQL cleanup, add curl smoke checks.

## Issues Encountered and Resolved

### 1. Port conflict on 5432
`make db-up` failed — port 5432 taken by `project-status-db` container.  
**Fix:** Changed `docker-compose.yml` default host port from 5432 → 5433 via `${DB_PORT:-5433}:5432`. Updated `api/.env.example` to match.

### 2. PostgreSQL 18 volume mount change
Container exited (1) after first successful start.  
**Fix:** PostgreSQL 18 changed the recommended mount from `/var/lib/postgresql/data` to `/var/lib/postgresql`. Updated `docker-compose.yml` volume mount. Ran `docker compose down -v` to clear the stale volume.

### 3. Alembic autogenerate included `drop_table('alembic_version')`
With `include_schemas=True`, Alembic scanned the `public` schema and detected `alembic_version` as a table to remove.  
**Fix:** Added `include_name` filter to `migrations/env.py` that restricts autogenerate comparison to the `agent_workbench` schema only.

### 4. Alembic env.py ignored sqlalchemy.url in tests
`_run_migrations()` called `alembic_cfg.set_main_option("sqlalchemy.url", ...)` but `env.py` reads from `DATABASE_URL` env var.  
**Fix:** Temporarily set `DATABASE_URL` + `APP_ENV` env vars in `_run_migrations()` before calling `command.upgrade()`, then restore.

### 5. SQLAlchemy 2.x: `lazy="dynamic"` removed
All API endpoints returned 500 with `InvalidRequestError: On relationship Project.sections, 'dynamic' loaders cannot be used`.  
**Fix:** Changed all `lazy="dynamic"` → `lazy="select"` in `projects/models.py`, `tasks/models.py`, `runs/models.py`. Service layer uses explicit `select()` queries and never traverses these relationships.

### 6. `make test` didn't load `.env`
Alembic migration in conftest failed because `DATABASE_URL` not set.  
**Fix:** Changed `make test` to `uv run --env-file .env pytest`.

## Key Decisions

- Local dev workflow: `api/.env` (gitignored) holds `DATABASE_URL` and `AGENT_WORKBENCH_TEST_DATABASE_URL`. All `uv run` commands use `--env-file .env`.
- `make migrate` runs `uv run --env-file .env alembic upgrade head` directly (not via Docker Compose migrations service).
- `make migrate-generate MSG="..."` for new migrations.
- Test strategy: session-scoped app + Alembic migrations; function-scoped `autouse` `clean_db` fixture truncates all tables via `TRUNCATE ... CASCADE` in reverse FK order.

## Validation

- `make lint` clean
- `make test` — 1 passed (health check)
- `make smoke` (with API server running) — 6/6 passed: health, GET/POST projects, GET/POST agents, POST events

## Commit

`0ed01d9` feat(db+test): first Alembic migration, pytest fixtures, smoke checks

## Next Steps

1. API contract tests for projects, tasks, agents modules.
2. Go CLI scaffold (Cobra + Viper).
3. Cloud review gate before real use.
