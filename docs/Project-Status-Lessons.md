# Project Status - Lessons Learned

Reusable lessons and patterns to adopt (or avoid) from `/shared/projects/dev/project-status`.

## What To Adopt

### Architecture

- **API-first monorepo** with `api/`, `web/`, `cli/` directories works well.
- **Flask application factory** pattern with blueprints provides clean separation.
- **Single data-access layer** (API only) prevents silent drift between clients.
- **Environment-driven configuration** (`APP_ENV`, `DATABASE_URL`) enables local/dev/stage/prod without code changes.

### Database

- **PostgreSQL 18** via Docker Compose for local development.
- **Alembic migrations** from day one; avoid runtime schema creation in production.
- **UUID primary keys** (as String(36)) work well for distributed/idempotent scenarios.
- **ARRAY columns** for tags are convenient for simple use cases.
- **Indexed query patterns** (`status`, `phase`, `created_at`) improve list performance.

### API Design

- **Health and readiness endpoints** (`/health`, `/ready`) provide deployment reliability.
- **Consistent error format** with `code`, `message`, `details` improves debugging.
- **Pagination with page/per_page** and total count is agent-friendly.
- **Request validation** with custom validators per field catches errors early.

### Testing

- **PostgreSQL 18** for tests. Do not use SQLite for any tests.
- **pytest fixtures** for `app`, `client`, and sample data are reusable.
- **Per-test database cleanup** via `autouse` fixture prevents test pollution.

### Docker Compose

- **Separate `migrations` service** ensures schema is current before API starts.
- **Health checks** with `pg_isready` prevent premature API startup.
- **Bind mounts** during dev enable hot reloading.

## What To Improve

### Data Model

- **Add `version` field** for optimistic locking; project-status lacks concurrency control.
- **Use `TIMESTAMPTZ`** instead of `TIMESTAMP` for timezone-aware timestamps.
- **Consider `GENERATED ALWAYS AS`** for derived columns to prevent stale data.

### API

- **Avoid path-based versioning at first**; prefer stable contracts with deprecation headers.
- **Return `422 Unprocessable Entity`** for validation errors, not `400 Bad Request`.
- **Add `source` enum validation** instead of allowing arbitrary strings.

### Configuration

- **Use `pydantic-settings`** for type-safe, validated configuration.
- **Fail fast on missing `DATABASE_URL`**; project-status raises `ValueError` in `Config` which is correct.

### Migrations

- **Use semantic revision IDs** (e.g., `001_initial`); project-status does this well.
- **Add `downgrade()` functions** even if rarely used; aids local development.

### Tests

- **Use PostgreSQL 18-backed tests**; project-status test fixtures use SQLite which misses PostgreSQL-specific behavior. Do not use SQLite for this project.
- **Test database session lifecycle**; project-status has circular import in `models.get_db_session()`.

### Documentation

- **Keep API docs in code or OpenAPI**; project-status uses separate markdown which can drift.
- **Document `_source` field meaning**; project-status doesn't clarify when it's set.

## Known Implementation Debt (Do Not Copy)

- Circular import in `models.py` `get_db_session()` function.
- Tests assert `400 or 422` indicating unclear validation error convention.
- No API versioning strategy documented.
- `init_db()` creates tables at startup; prefers migrations-only in production.
- `short_name` uniqueness constraint lacks helpful error message.
- No idempotency keys for retry-safe agent operations.

## Agent Workbench Specific Adaptations

- Add **multi-project support** from the start with `project_id` foreign keys.
- Add **sections/modules** as first-class resources, not just tags.
- Add **task leases** with heartbeat/expiration for safe agent coordination.
- Add **append-only event history** for auditability.
- Add **idempotency key** support for agent-submitted actions.
- Add **optimistic locking** via `version` column on mutable resources.

Last updated: 2026-05-22
