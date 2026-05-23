# Session: API Contract Tests

**Date:** 2026-05-22  
**Agent:** claude-sonnet-4-6 (session 4)  
**Tasks:** API contract tests for projects, tasks, agents modules

## Objective

Add API route contract tests covering CRUD, optimistic locking, and the full task lease lifecycle (claim → heartbeat → complete/block).

## Tests Written

### `api/tests/test_projects.py`
- ListProjects: empty list, returns created project, pagination
- CreateProject: required fields, missing name/slug → 422, slug unique → 409, optional fields stored
- GetProject: returns project, 404, 400 invalid UUID
- UpdateProject: updates name + increments version, requires version → 422, version conflict → 409, slug conflict → 409, 404

### `api/tests/test_tasks.py`
- ListTasks: empty, returns created task, status filter, 404 unknown project
- CreateTask: required title, missing title → 422, optional fields stored
- GetTask: returns task, 404
- UpdateTask: updates title + version, version conflict → 409
- TaskLeaseLifecycle: claim sets claimed_by, double-claim same agent succeeds, different agent → 409, heartbeat extends lease, wrong agent heartbeat → 409, complete clears lease, complete wrong agent → 409, block sets status, missing agent_name → 422

### `api/tests/test_agents.py`
- ListAgents: empty, returns created agent
- CreateAgent: required fields, missing name → 422, defaults agent_type to "local", name unique → 409, optional fields stored
- GetAgent: returns agent, 404, 400 invalid UUID
- UpdateAgent: updates + version, requires version → 422, version conflict → 409

## Issues Found and Fixed

### 1. `lazy="dynamic"` removed in SQLAlchemy 2.x (found via smoke checks, fixed in session 3)
All relationship back-references changed to `lazy="select"`.

### 2. Flask-SQLAlchemy 3.x session scoping causes `idle in transaction` hang
**Root cause**: Flask-SQLAlchemy 3.x scopes the session to the APP context, not per-request. With a session-scoped `app` fixture, the session stays open across tests. After `test_empty`'s GET /api/agents, the scoped session holds a connection in "idle in transaction" state (read-only routes don't commit). When `clean_db` pushes a new app context and runs `TRUNCATE`, it blocks waiting for the exclusive lock held by the "idle in transaction" connection.

**Fix**: Changed `clean_db` to run BEFORE each test (not after). Added explicit `_db.session.rollback() + _db.session.remove()` before the TRUNCATE to release the lingering connection. Use `_db.engine.connect()` directly (raw engine connection) for the TRUNCATE to bypass the scoped session entirely.

**Key**: Flask-SQLAlchemy 3.x teardown happens on app context teardown, not per-request teardown. For test setups with a session-scoped app context, callers must manually manage session lifecycle between tests.

### 3. test_requires_agent_type incorrect
`create_agent` service defaults `agent_type` to `"local"` when not provided. Test was wrong — changed to `test_defaults_agent_type_to_local`.

## Status

Tests written, awaiting single clean run to verify all pass. If failures exist, will fix before committing.

## Next Steps

1. Verify all 50 tests pass in clean run.
2. Commit test files.
3. Update TODO.md / MEMORY.md.
4. Go CLI scaffold (next major task).
