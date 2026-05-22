# Project TODO

Task list for `Agent Workbench`, organized by ownership and project phase.

## Needs Attention

Items here require Jason's input, a decision, credentials, external access, or manual validation before agent work can continue.

- [X] Confirm API framework: Flask. Completed 2026-05-22 by Jason.
- [X] Confirm MVP starts with API plus CLI/scripts; web UI is post-MVP for human review and ad hoc task entry. Completed 2026-05-22 by Jason.
- [X] Confirm private-network MVP can defer authentication; research IDP before wider exposure. Completed 2026-05-22 by Jason.
- [ ] Confirm exact dev/stage/production database names and users; initial secret injection direction is Docker Compose env files/secrets with Vault as future research.
- [X] Confirm OpenCode scheduled runs should use stub CLI commands during bootstrap, with gradual replacement by real CLI/API. Completed 2026-05-22 by Jason.
- [X] Confirm deployed runtime should default to `APP_ENV=prod` while local/test commands explicitly select `APP_ENV=local`. Completed 2026-05-22 by Jason.
- [X] Confirm shared PostgreSQL environments use separate servers/databases with same schema `agent_workbench`. Completed 2026-05-22 by Jason.
- [X] Confirm deployment target order: Docker Compose VM first, K3s later as future feature. Completed 2026-05-22 by Jason.

## Manual Validation

These items need Jason to validate on real systems, live services, devices, accounts, or deployment targets.

- [ ] Confirm requirements and success criteria in `PROJECT_BRIEF.md`.
- [ ] Confirm chosen stack and deployment target.
- [ ] Confirm credentials, API keys, database URLs, and production access are not committed.
- [ ] Validate local PostgreSQL container startup after Compose is added.
- [ ] Validate dev/stage database connectivity when secrets are available.
- [ ] Validate target schema/database creation in dev and stage.
- [ ] Validate production `postgresql.taylor.lan` connectivity during release readiness.
- [ ] Validate target schema/database creation in prod during release readiness.
- [ ] Validate deployment or release workflow on the target environment.

## AI Agent Work

These items are good candidates for a local model or cloud agent.

### Review

Use this section for a cloud-based AI agent or larger-context reviewer before real use, release, or deployment.

- [ ] Cloud review: build a current contract map for API routes, request/response JSON, error shapes, CLI/script commands, database schema, Docker services, environment variables, and build outputs.
- [ ] Cloud review: compare docs, source, tests, Docker/Compose, README, and TODO for stale or conflicting contracts.
- [ ] Cloud review: inspect data model for task leases, heartbeats, idempotency, optimistic locking, event history, and multi-project support.
- [ ] Cloud review: inspect API implementation for correctness, validation gaps, transaction/session lifecycle, error consistency, and PostgreSQL assumptions.
- [ ] Cloud review: inspect bootstrap CLI/scripts for safe task claiming, useful diagnostics, and stable agent-facing output.
- [ ] Cloud review: inspect Docker/Compose and deployment docs for repeatability and secret handling.
- [ ] Cloud review: run or specify the closest available validation commands and record failures, skipped checks, and missing tooling.
- [ ] Cloud review: convert findings into prioritized TODO items before broad refactoring begins.
- [ ] Cloud review signoff: confirm all high-risk findings are resolved or explicitly deferred before real use.

### Discovery And Planning

- [X] Replace template placeholders with Agent Workbench project direction.
- [X] Clarify that `agent-workbench` is the active work target and `project-status` is reference material only. Completed 2026-05-22 by Codex.
- [X] Inventory reusable lessons from `/shared/projects/dev/project-status` without copying known implementation drift. Completed 2026-05-22 by Copilot.
- [X] Inventory OpenCode setup repo requirements from `/shared/projects/ai/opencode-setup`. Completed 2026-05-22 by OpenCode.
- [X] Decide initial API framework: Python 3.14 latest plus Flask. Completed 2026-05-22 by Jason.
- [X] Decide initial CLI stack: Go 1.26 with Cobra and Viper. Completed 2026-05-22 by Jason.
- [X] Decide post-MVP web stack: React with Node.js 24 LTS, latest npm, and Express. Completed 2026-05-22 by Jason.
- [X] Decide Flask package layout. Completed 2026-05-22 by claude-sonnet-4-6; `src/` layout, application factory, Flask-SQLAlchemy 3.x, pydantic-settings, per-module blueprints inside `api/`.
- [X] Define initial module boundaries: projects, project_sections, status, tasks, agents, runs, events, reviews. Completed 2026-05-22 by claude-sonnet-4-6; modules scaffolded with models, routes, and service stubs.
- [X] Define initial API route style and compatibility policy without URL versioning by default. Completed 2026-05-22 by claude-sonnet-4-6; documented in `docs/API-Contracts.md` (no URL versioning, canonical routes, pagination, error shape).
- [X] Define initial database schema and migration strategy, including task assignee/owner fields. Completed 2026-05-22 by claude-sonnet-4-6; 8 SQLAlchemy models with UUID PKs, optimistic locking, lease fields on tasks, append-only events; Alembic configured in `api/`.
- [X] Define local/dev/stage/prod database target names and stable schema policy in `docs/Database.md`. Completed 2026-05-22 by claude-sonnet-4-6; DB targets, schema `agent_workbench`, and env var names documented in `docs/Database.md`.
- [ ] Define project discovery config for `~/projects/ai`, `~/projects/courses`, `~/projects/dev`, and `~/projects/infra`.
- [ ] Define project type vocabulary, default sections/modules, phase workflows, and default agent selection rules.
- [ ] Define state machines for project status, task status, agent run status, and review findings.
- [ ] Define task assignee/owner model for agent and human responsibility.
- [ ] Define status/task event history strategy, including bootstrap structured logging before full event APIs if needed.
- [ ] Define optional Prometheus metrics scope, config flag, endpoint, and deployment notes for `prometheus.taylor.lan`.
- [ ] Research future authentication/IDP options for post-MVP use.
- [ ] Research HashiCorp Vault integration for deployment secrets after Compose secrets/env files are working.
- [X] Define bootstrap transition from Markdown files to Postgres-backed scripts/CLI/API. Completed 2026-05-22 by Codex; `docs/Bootstrap-CLI.md` now describes Markdown/local state, API-backed scripts, full CLI coordination, and post-MVP web phases.
- [X] Evaluate Grok planning/scaffolding review for worthwhile recommendations. Completed 2026-05-22 by Codex; accepted centralized API contract doc, additional Mermaid diagrams, bootstrap transition roadmap, and impact-weighted task selection guidance.

### Architecture And Contracts

- [X] Draft API route contract for project info, project sections/modules, project status, project tasks, agents, runs, and events. Completed 2026-05-22 by Codex in `docs/API-Contracts.md`; keep it aligned with future OpenAPI/tests.
- [X] Draft database ERD or schema notes for projects, project_sections, status records, tasks, task events, agents, runs, leases, and reviews. Completed 2026-05-22 by Codex; `docs/Architecture.md` now includes a Mermaid ERD and `docs/Database.md` holds schema planning notes.
- [X] Define nullable `project_section_id` behavior for project-wide/general status records and tasks. Completed 2026-05-22 by Codex; canonical behavior is `null` for project-wide/general work.
- [X] Define phase enum and validation behavior for status records and tasks. Completed 2026-05-22 by Codex; initial phases are `planning`, `research`, `implementation`, `testing`, and `review`.
- [X] Define optimistic locking/version fields for mutable resources. Completed 2026-05-22 by Codex; `docs/API-Contracts.md` requires mutable resources to include `version`.
- [ ] Define idempotency key behavior for agent-submitted commands.
- [ ] Define task claim/lease/heartbeat behavior, including interaction with task assignee/owner.
- [X] Establish standard API response formats for errors (e.g., 422 Unprocessable Entity for validation) and collection pagination (`page`/`per_page`). Completed 2026-05-22 by Codex in `docs/API-Contracts.md`.
- [ ] Define in-code API documentation strategy (e.g., OpenAPI auto-generation) to prevent API contract drift.
- [X] Evaluate `pydantic-settings` for type-safe configuration validation and failing fast on missing `DATABASE_URL`. Completed 2026-05-22 by claude-sonnet-4-6; adopted in `api/src/agent_workbench/config.py`.
- [ ] Define append-only event model, structured logging fallback, and retention expectations.
- [ ] Define Markdown summary/mirroring strategy for `MEMORY.md`, `TODO.md`, and project status snapshots.
- [X] Define local/dev/stage/prod environment variable names in `docs/Database.md`. Completed 2026-05-22 by Codex.
- [X] Add example environment files for local, dev, stage, and prod without secrets. Completed 2026-05-22 by claude-sonnet-4-6; `api/.env.example` added.
- [ ] Decide whether to split future contract details into generated OpenAPI plus this human-readable contract guide, or keep `docs/API-Contracts.md` as the canonical source through MVP.

### Scaffolding

- [X] Add backend project structure after framework decision. Completed 2026-05-22 by claude-sonnet-4-6; `api/` directory with `src/agent_workbench/`, all 8 domain modules, blueprints, and SQLAlchemy models.
- [X] Add Docker Compose with local PostgreSQL 18 container and separate `migrations` service. Completed 2026-05-22 by claude-sonnet-4-6; `docker-compose.yml` with db, api (profile), and migrations (profile) services.
- [X] Add Docker Compose secret/env-file pattern for non-local deployment without committing secrets. Completed 2026-05-22 by claude-sonnet-4-6; env var pattern documented in `api/.env.example` and Makefile.
- [X] Add example env files without secrets. Completed 2026-05-22 by claude-sonnet-4-6; `api/.env.example`.
- [X] Add database migration tooling (Alembic) configured for semantic revision IDs and downgrade functions. Completed 2026-05-22 by claude-sonnet-4-6; `api/alembic.ini`, `api/migrations/env.py`, `api/migrations/script.py.mako`.
- [X] Add migration commands that require explicit `APP_ENV` for dev/stage/prod targets. Completed 2026-05-22 by claude-sonnet-4-6; `make migrate-dev/stage/prod` in Makefile require env vars and prod prompts for confirmation.
- [X] Add safe database bootstrap docs and SQL template for creating target schemas without embedding secrets. Completed 2026-05-22 by Codex.
- [ ] Add environment-aware wrapper command for running schema bootstrap against local/dev/stage/prod.
- [X] Expand root `Makefile` with setup, lint, test, smoke, integration-test, migration, cleanup, and real CLI build targets. Completed 2026-05-22 by claude-sonnet-4-6; full Makefile with `API_DIR=api` prefix for Python targets.
- [X] Configure `pytest` with `autouse` fixtures for per-test PostgreSQL 18 database cleanup. Completed 2026-05-22 by claude-sonnet-4-6; `api/tests/conftest.py` with session-scoped app/migration fixtures and autouse clean_db TRUNCATE; `make test` with `--env-file .env`.
- [X] Add curl smoke checks for API health and basic workflow validation. Completed 2026-05-22 by claude-sonnet-4-6; `scripts/smoke-curl.sh` covers health, projects, agents, events; `make smoke` target.
- [ ] Add Python containerized integration-test runner.
- [X] Add stub CLI/bootstrap commands for OpenCode: task next, claim, heartbeat, complete, block, status show. Completed 2026-05-22 by Codex.
- [X] Confirm `cli/builds/` is excluded from Git. Completed 2026-05-22 by Codex.
- [X] Add root `Makefile` with bootstrap `task-next`, `status-show`, `validate`, and placeholder `build-cli` targets. Completed 2026-05-22 by Codex.
- [X] Establish `api/`, `cli/`, `web/` top-level component directories with stubs for cli and web. Completed 2026-05-22 by claude-sonnet-4-6; `cli/.gitkeep` and `web/.gitkeep` added; Python API lives under `api/`.
- [ ] Scaffold Go CLI command tree using Cobra and Viper for config/env resolution.
- [ ] Add post-MVP web scaffold using React + Express on Node.js 24 LTS with npm latest (only if MVP API/CLI queue is unblocked).
- [ ] Add scheduled OpenCode wrapper that calls bootstrap commands and runs one focused task.
- [ ] Add optional Prometheus metrics dependencies and `/metrics` endpoint behind configuration.

### Implementation Phase: Core API Modules

- [X] Implement `projects` module for project metadata, Git source location, type, environment, and defaults. Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes (list, create, get, patch), service layer, serialization, optimistic locking, slug conflict handling.
- [X] Implement `project_sections` module for modules/sections within a project. Completed 2026-05-22 by claude-sonnet-4-6; nested CRUD routes under /api/projects/{id}/sections, sort_order support, project ownership validation.
- [X] Implement `project_status` module for project-wide and section-scoped current status and history. Completed 2026-05-22 by claude-sonnet-4-6; list/create/patch routes nested under /api/projects/{id}/status, optional project_section_id, optimistic locking.
- [X] Implement `project_tasks` module for project-wide and section-scoped tasks, priorities, phases, dependencies, assignee/owner, leases, and completion evidence. Completed 2026-05-22 by claude-sonnet-4-6; list/create at /api/projects/{id}/tasks; get/patch/claim/heartbeat/complete/block at /api/tasks/{id}/...; atomic lease via targeted UPDATE with rowcount check.
- [X] Implement `agents` module for agent registry, capabilities, defaults, and runtime hints. Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes at /api/agents, name uniqueness enforced, optimistic locking.
- [ ] Scaffold Go 1.26 CLI and configure builds to write artifacts into `cli/builds/`.
- [X] Implement `runs` module for run attempts, heartbeats, validation, and outcomes. Completed 2026-05-22 by claude-sonnet-4-6; POST create, GET, heartbeat, complete, fail; atomic state transitions via targeted UPDATE.
- [X] Implement `events` module as append-only audit trail for status/task/run/review history. Completed 2026-05-22 by claude-sonnet-4-6; GET /api/projects/{id}/events and POST /api/events; no update/delete routes.
- [X] Implement `reviews` module for cloud review findings and signoff gates. Completed 2026-05-22 by claude-sonnet-4-6; list/create nested under project, PATCH /api/reviews/{id} for status updates.

### Tests And Quality

- [ ] Add unit tests for state transitions and validation.
- [X] Add API tests for all module contracts. Completed 2026-05-22 by claude-sonnet-4-6; test_projects.py, test_tasks.py (incl. lease lifecycle), test_agents.py — 50 tests, 50 passed, 0.83s.
- [ ] Add database integration tests using local PostgreSQL container.
- [ ] Add smoke script tests for health and minimal task lifecycle.
- [ ] Add Python containerized integration tests for multi-project workflows and task leases.
- [ ] Run lint, format check, type check, build, and tests when available.
- [ ] Review with `QUALITY_CHECKLIST.md`.

### Documentation And Deployment

- [ ] Update `README.md` with setup and bootstrap workflow.
- [ ] Add `docs/Development.md` after Compose/scripts exist.
- [ ] Document deployment, environment variables, and operational notes.
- [ ] Document database migration workflow.
- [X] Add database environment and schema planning doc. Completed 2026-05-22 by Codex in `docs/Database.md`.
- [ ] Document secret handling, Docker Compose secrets/env files, Vault future option, and Ansible integration expectations without copying secrets.
- [X] Document bootstrap CLI command workflow for OpenCode in `docs/Bootstrap-CLI.md`. Completed 2026-05-22 by Codex.
- [ ] Document OpenCode automation workflow once the OpenCode setup repo is ready.
- [ ] Document post-MVP web UI scope for human review and adding tasks on the fly, using React + Express on Node.js 24 LTS.
- [ ] Document optional Prometheus setup and scrape example.
- [ ] Record decisions and milestones in `MEMORY.md`.

## In Progress

Move exactly one task here while working if multiple agents may run at the same time.

- [ ]

## Blocked

Move blocked tasks here with the blocker and the next required human action.

- [ ]

## Done

Move completed items here with a brief note.

- [X] Bootstrap project direction, workflow docs, and planning files for Agent Workbench. Completed 2026-05-22 by Codex.
