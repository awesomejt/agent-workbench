## Prompt

Great, I had Claude Code implement the API section. Review the agent-workbench repo. Look for code quality and style, software design decisions, and the code itself. Make a list of recommendations to consider before moving on to the CLI client.

## Response

**✅ Code Review: agent-workbench API (Post-Claude Implementation)**

The repo has been updated with a solid, production-oriented **Flask + SQLAlchemy** API in the `api/` directory. This is a significant step forward from the previous Markdown/bootstrap stubs.

### Overall Assessment
- **Strengths**: Excellent modular structure, strong configuration, good use of Alembic, thoughtful error handling, and alignment with the documented architecture. The code is clean, well-organized, and follows modern Python practices.
- **Maturity**: Early but high-quality MVP foundation. Core patterns (especially for tasks/leases) are in place.
- **Style**: Consistent, readable, with good separation of concerns (models, routes, services).

### Detailed Code Quality & Style
**Positives**:
- **Structure**: `src/agent_workbench/` with submodules (`projects/`, `tasks/`, `runs/`, `events/`, etc.) + Blueprints is exactly right for a modular monolith.
- **Configuration**: Pydantic `Settings` with validators + env-file support is excellent.
- **Database**: Custom `Base` with schema and naming conventions for consistency. `SCHEMA = "agent_workbench"` is smart.
- **Entry point**: Clean `create_app()` factory + `main()` CLI entry.
- **Dependencies**: `pyproject.toml` with `uv`, Ruff, mypy, pytest — modern and lean.
- **Docker/Make**: `Dockerfile`, `docker-compose.yml`, and comprehensive `Makefile` show strong dev experience focus.

**Areas for Improvement**:
- **Framework note**: Code uses **Flask** (as implemented), while earlier docs mentioned considering FastAPI. Flask is fine for MVP, but FastAPI would give automatic OpenAPI + better Pydantic integration out-of-the-box.
- **Some modules are stubs**: `tasks/` is fleshed out; others (`projects/`, `agents/`, etc.) appear lighter.
- **Error handling**: Centralized, but could expand with more specific domain exceptions.
- **Testing**: Directory exists but coverage appears minimal so far.

### Key Files Review

1. **app.py** — Good factory pattern, blueprint registration. Minor: `Flask` debug mode tied to env is correct.
2. **config.py** — Strong. Validator for `app_env` is perfect.
3. **database.py** — Professional naming conventions and schema isolation.
4. **tasks/** (models, routes, service) — This is the strongest part. Lease/claim logic, heartbeats, and state transitions look thoughtful and safe.

### Recommendations Before Moving to CLI Client

Here is a prioritized list:

**High Priority (Do Before CLI)**
1. **Complete Data Models** — Ensure all core tables (projects, tasks with `lease_expires_at`, `claimed_by`, events as append-only, runs, etc.) have full models + relationships. Add indexes on `status`, `lease_expires_at`, `project_path`.
2. **Lease Safety** — In `tasks/service.py`, double-check atomic claim (use `SELECT FOR UPDATE` or optimistic locking with version column) to prevent race conditions.
3. **API Contracts** — Add Pydantic request/response models (even with Flask) and document them in `docs/API.md`. Export OpenAPI spec manually if sticking with Flask.
4. **Environment & Secrets** — Strengthen secret_key handling (never use default in prod). Add more env validation.
5. **Migrations** — Run and verify initial Alembic migrations. Add a baseline migration if needed.

**Medium Priority**
- **Logging & Observability** — Add structured logging (e.g., structlog) and request ID middleware.
- **Authentication** — Add simple API key or JWT for agents (even if internal for now).
- **Input Validation** — Use Flask-WTF or manual Pydantic validation on routes.
- **Testing** — Add basic pytest fixtures for DB + test core flows (claim → heartbeat → complete).
- **Error Responses** — Standardize JSON error format across all endpoints.
- **Health & Readiness** — Expand `/health` to include DB connectivity check.

**Lower Priority / Nice-to-Haves**
- Consider migrating to FastAPI later for better async + auto-docs.
- Add rate limiting.
- Prometheus metrics (as planned).
- More comprehensive `QUALITY_CHECKLIST.md` enforcement in CI (once GitHub Actions are added).

**CLI Transition Readiness**
The API is now in good shape for a thin Go CLI (Cobra) to consume it. Focus CLI on:
- `task next/claim/heartbeat/complete`
- Project discovery
- Status sync

**Summary**: This is a **high-quality implementation** for an early-stage agent coordination backend. Claude did a good job respecting the architecture and agent-safety requirements (leases, events, modularity). With the above items addressed, you'll have a robust foundation for the Go CLI and future web UI.

Would you like me to:
- Dive deeper into a specific module (e.g., full review of `tasks/` code)?
- Suggest specific refactors or draft improvements?
- Help with model expansions or test scaffolding?

Just share any particular files or concerns!