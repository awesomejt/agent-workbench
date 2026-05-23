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

- [X] Cloud review: build a current contract map for API routes, request/response JSON, error shapes, CLI/script commands, database schema, Docker services, environment variables, and build outputs. Completed 2026-05-22 by Codex.
- [X] Cloud review: compare docs, source, tests, Docker/Compose, README, and TODO for stale or conflicting contracts. Completed 2026-05-22 by Codex.
- [X] Cloud review: inspect data model for task leases, heartbeats, idempotency, optimistic locking, event history, and multi-project support. Completed 2026-05-22 by Codex.
- [X] Cloud review: inspect API implementation for correctness, validation gaps, transaction/session lifecycle, error consistency, and PostgreSQL assumptions. Completed 2026-05-22 by Codex.
- [X] Cloud review: inspect bootstrap CLI/scripts for safe task claiming, useful diagnostics, and stable agent-facing output. Completed 2026-05-22 by Codex.
- [X] Cloud review: inspect Docker/Compose and deployment docs for repeatability and secret handling. Completed 2026-05-22 by Codex.
- [X] Cloud review: run or specify the closest available validation commands and record failures, skipped checks, and missing tooling. Completed 2026-05-22 by Codex; ruff lint passes, ruff format fails (15 files), mypy fails (17 errors), pytest passes (54 tests), go vet passes, clean-clone build fails due to gitignore issue.
- [X] Cloud review: convert findings into prioritized TODO items before broad refactoring begins. Completed 2026-05-22 by Codex; findings recorded in `docs/reviews/2026-05-22-1741-codex-cli-repo-recommendations.md` and added to pre-dogfood fix list below.
- [X] Cloud review signoff: confirm all high-risk findings are resolved or explicitly deferred before real use. Completed 2026-05-23 by claude-sonnet-4-6. All three explicitly-named highest-risk items resolved: (1) ignored `cli/internal/output` package → renamed to `render` (P0, da937e6); (2) task selection not agent-safe → `available=true` filter added (P1, f98cc15); (3) event/idempotency behavior not matching implementation → auto-append events (P2) + idempotency table (P2, ea75a71). All P0–P3 pre-dogfood fixes complete. Medium-priority items (OpenAPI strategy, bootstrap transition, CLI ergonomics like `--output` validation and timeout) are explicitly deferred to post-MVP; none block real use.

### Codex Review: Pre-Dogfood Fixes

Items required before using agent-workbench to manage its own development. Ordered by priority.

**P0 — Build-breaking and crash risks**

- [X] Fix `.gitignore` global `output/` rule silently ignoring `cli/internal/output/output.go`; rename directory to `cli/internal/render` and update all import paths. Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.
- [X] Fix CLI nil pointer dereference: `task_claim.go` dereferences `*task.ClaimedBy` without a nil check; crashes on any unassigned task. Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.
- [X] Fix CLI double-error printing: commands return `err` to Cobra while also calling `output.Err`; results in duplicate error messages on stderr. Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.
- [X] Trim trailing slashes from `--api-url` in the API client to prevent malformed URLs like `http://host//api/...`. Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.

**P1 — Quality gate and product correctness**

- [X] Run `ruff format` across all Python source files (15 files currently fail format check); add format check to `make validate`. Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.
- [X] Fix 17 mypy errors; decide and document mypy strictness policy for Flask-SQLAlchemy and rowcount typing patterns; add `make type-check` to `make validate`. Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.
- [X] Make `awb task next` and `awb task list` lease-aware: add `available=true` API filter meaning `status=pending AND (claimed_until IS NULL OR claimed_until < now())`; update CLI flags accordingly. Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.
- [X] Fix `root/.env.example.local` to use port 5433 and password `agent_workbench_local` to match `api/.env.example` and Docker Compose. Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.

**P2 — Audit trail, reliability, and API correctness**

- [X] Auto-append events on task lifecycle transitions (claim, heartbeat, complete, block) within the same DB transaction as the state change; add tests verifying both state change and event creation. Completed 2026-05-22 by claude-sonnet-4-6; events/service._record() helper; 5 new tests in test_tasks.py.
- [X] Auto-append events on run transitions (heartbeat, complete, fail) within the same DB transaction; add tests. Completed 2026-05-22 by claude-sonnet-4-6; 4 new tests in test_runs.py.
- [X] Define and implement idempotency behavior: scope to endpoint + actor + key rather than a single task column; update API and CLI to send and replay idempotency keys on claim/heartbeat/complete/block. Completed 2026-05-23 by claude-sonnet-4-6; new idempotency_keys table + service; Idempotency-Key header on claim/heartbeat/complete/block; CLI auto-generates UUID per invocation; 7 new tests in test_idempotency.py.
- [X] Add API validation: `duration_seconds` must be a positive integer within a reasonable range; return 422 on invalid input. Completed 2026-05-22 by claude-sonnet-4-6; 1–604800s range enforced in claim and heartbeat routes.
- [X] Add API validation: `project_section_id` on tasks must belong to the same project; return 422 on mismatch. Completed 2026-05-22 by claude-sonnet-4-6; validated on task create and update.
- [X] Add API validation: `task_id` on run creation must belong to the provided project; return 422 on mismatch. Completed 2026-05-22 by claude-sonnet-4-6; project existence and task ownership validated in runs/routes.py.
- [X] Add enum validation for task status, phase, review status, and review severity fields; return 422 with field-level error details. Completed 2026-05-22 by claude-sonnet-4-6; frozenset constants in tasks/routes.py and reviews/routes.py; 5 new tests.
- [X] Decide and document whether `task block` should clear the lease like `task complete` does, or hold it intentionally; implement and test the chosen behavior. Completed 2026-05-22 by claude-sonnet-4-6; decision: block clears lease (agent gives up the task; it stays blocked until reset to pending); 1 new test confirms claimed_by/claimed_until both null after block.
- [X] Add `make cli-test` target (`cd cli && go test ./...`); add `make cli-clean-build-check` target that builds from a `git archive` to catch future gitignore issues. Completed 2026-05-22 by claude-sonnet-4-6 (P0/P1 session).
- [X] Add a friendly hint to `make test` when the local PostgreSQL container is not reachable. Completed 2026-05-22 by claude-sonnet-4-6; pg_isready pre-check with actionable message.

**P3 — CLI expansion for full agent session coverage**

- [X] Add `awb run start/get/heartbeat/complete/fail` commands so every agent session can create a durable run record and heartbeat through it. Completed 2026-05-22 by claude-sonnet-4-6.
- [X] Add `awb event list/append` commands for debugging and audit trail inspection. Completed 2026-05-22 by claude-sonnet-4-6; event list supports --limit, append accepts --type/--task/--run/--actor-name/--payload.
- [X] Add `awb agent list/create/get/update` commands for agent registry management. Completed 2026-05-22 by claude-sonnet-4-6.
- [X] Add `awb project create/get/update` and `awb section list/create/get/update` commands for project and section administration. Completed 2026-05-22 by claude-sonnet-4-6.
- [X] Add `awb status create/update` commands for project/section status management from the CLI. Completed 2026-05-22 by claude-sonnet-4-6; status show now includes ID column for use with update.
- [X] Add shell completion (`awb completion bash/zsh/fish/powershell`) with inline install instructions. Completed 2026-05-22 by claude-sonnet-4-6.

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
- [ ] Dogfood: register agent-workbench as its own project in the workbench once pre-dogfood fixes are done; use `awb` to manage all remaining implementation tasks instead of editing TODO.md directly.
- [ ] Define project discovery config for `~/projects/ai`, `~/projects/courses`, `~/projects/dev`, and `~/projects/infra`.
- [ ] Define project type vocabulary, default sections/modules, phase workflows, and default agent selection rules.
- [ ] Define state machines for project status, task status, agent run status, and review findings.
- [ ] Define task assignee/owner model for agent and human responsibility.
- [ ] Define task duration estimation model: t-shirt sizing (XS/S/M/L/XL) or Agile story points mapped to seconds, with agent-capability multipliers (cloud vs. local AI) so lease windows auto-scale without manual `estimated_duration_seconds` on every task.
- [ ] Define status/task event history strategy, including bootstrap structured logging before full event APIs if needed.
- [ ] Define optional Prometheus metrics scope, config flag, endpoint, and deployment notes for `prometheus.taylor.lan`.
- [ ] Add runtime metrics fields to `runs` table: `model_id`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `prompt_category` — to inform lease duration tuning and model selection heuristics.
- [ ] Create `benchmark-harness` as a separate project: structured AI agent evaluation with prompt libraries, scoring rubrics, and comparison reports; consumes agent-workbench API as infrastructure.
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
- [X] Scaffold Go CLI command tree using Cobra and Viper for config/env resolution. Completed 2026-05-22 by claude-sonnet-4-6; `awb` binary with task (next/list/get/claim/heartbeat/complete/block), project list, status show, version; builds to cli/builds/awb.
- [X] Add CLI install script and user-level config path support. Completed 2026-05-22 by claude-sonnet-4-6; `scripts/install-awb.sh` installs to `~/.local/bin` or `~/bin`; config now resolves `~/.config/awb` (preferred) then `~/.config/agent-workbench`; yaml/json/toml all supported; `make install-cli` target added.
- [ ] Add post-MVP web scaffold using React + Express on Node.js 24 LTS with npm latest (only if MVP API/CLI queue is unblocked).
- [ ] Add scheduled OpenCode wrapper that calls bootstrap commands and runs one focused task.
- [ ] Add optional Prometheus metrics dependencies and `/metrics` endpoint behind configuration.

### Implementation Phase: Core API Modules

- [X] Implement `projects` module for project metadata, Git source location, type, environment, and defaults. Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes (list, create, get, patch), service layer, serialization, optimistic locking, slug conflict handling.
- [X] Implement `project_sections` module for modules/sections within a project. Completed 2026-05-22 by claude-sonnet-4-6; nested CRUD routes under /api/projects/{id}/sections, sort_order support, project ownership validation.
- [X] Implement `project_status` module for project-wide and section-scoped current status and history. Completed 2026-05-22 by claude-sonnet-4-6; list/create/patch routes nested under /api/projects/{id}/status, optional project_section_id, optimistic locking.
- [X] Implement `project_tasks` module for project-wide and section-scoped tasks, priorities, phases, dependencies, assignee/owner, leases, and completion evidence. Completed 2026-05-22 by claude-sonnet-4-6; list/create at /api/projects/{id}/tasks; get/patch/claim/heartbeat/complete/block at /api/tasks/{id}/...; atomic lease via targeted UPDATE with rowcount check.
- [X] Implement `agents` module for agent registry, capabilities, defaults, and runtime hints. Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes at /api/agents, name uniqueness enforced, optimistic locking.
- [X] Add per-task `estimated_duration_seconds` for local-AI-friendly lease windows. Completed 2026-05-22 by claude-sonnet-4-6; 3-level resolution (request > task estimate > 1800s default); 4 new tests.
- [X] Harden config: reject default SECRET_KEY in prod; add DB connectivity check to /health (503 on failure). Completed 2026-05-22 by claude-sonnet-4-6.
- [X] Scaffold Go 1.26 CLI and configure builds to write artifacts into `cli/builds/`. Completed 2026-05-22 by claude-sonnet-4-6.
- [X] Implement `runs` module for run attempts, heartbeats, validation, and outcomes. Completed 2026-05-22 by claude-sonnet-4-6; POST create, GET, heartbeat, complete, fail; atomic state transitions via targeted UPDATE.
- [X] Implement `events` module as append-only audit trail for status/task/run/review history. Completed 2026-05-22 by claude-sonnet-4-6; GET /api/projects/{id}/events and POST /api/events; no update/delete routes.
- [X] Implement `reviews` module for cloud review findings and signoff gates. Completed 2026-05-22 by claude-sonnet-4-6; list/create nested under project, PATCH /api/reviews/{id} for status updates.

### Tests And Quality

- [X] Add unit tests for state transitions and validation. Completed 2026-05-23 by claude-sonnet-4-6; TestTaskStateMachineGuards (6 tests: cannot claim completed/blocked, cannot complete/block unclaimed, status/evidence on complete and block) + TestAvailableFilter (3 tests); total 101 tests, all pass.
- [X] Add API tests for all module contracts. Completed 2026-05-22 by claude-sonnet-4-6; test_projects.py, test_tasks.py (incl. lease lifecycle + duration), test_agents.py — 54 tests, 54 passed, 0.89s.
- [ ] Add database integration tests using local PostgreSQL container.
- [ ] Add smoke script tests for health and minimal task lifecycle.
- [ ] Add Python containerized integration tests for multi-project workflows and task leases.
- [X] Run lint, format check, type check, build, and tests when available. Completed 2026-05-23 by claude-sonnet-4-6; make validate (ruff + mypy) and make test (101 tests) both pass; make cli-vet passes.
- [ ] Review with `QUALITY_CHECKLIST.md`.

### Documentation And Deployment

- [X] Update `README.md` with setup and bootstrap workflow. Completed 2026-05-23 by claude-sonnet-4-6; quick start, CLI usage, project structure, module table, bootstrap fallback section.
- [X] Add `docs/Development.md` after Compose/scripts exist. Completed 2026-05-23 by claude-sonnet-4-6; prerequisites, first-time setup, daily workflow, CLI config, migrations, environment variables, project structure, dogfood workflow, secrets policy.
- [X] Document deployment, environment variables, and operational notes. Completed 2026-05-23 by claude-sonnet-4-6; covered in `docs/Development.md` (API/CLI/Makefile env vars, DB targets, secrets policy).
- [X] Document database migration workflow. Completed 2026-05-23 by claude-sonnet-4-6; covered in `docs/Development.md` (local, dev, stage, prod migration commands).
- [X] Add database environment and schema planning doc. Completed 2026-05-22 by Codex in `docs/Database.md`.
- [X] Document secret handling, Docker Compose secrets/env files, Vault future option, and Ansible integration expectations without copying secrets. Completed 2026-05-23 by claude-sonnet-4-6; `docs/Secrets.md` covers local dev, Compose env files, non-local migration injection, SECRET_KEY policy, Ansible boundary, and Vault future path.
- [X] Document bootstrap CLI command workflow for OpenCode in `docs/Bootstrap-CLI.md`. Completed 2026-05-22 by Codex.
- [ ] Document OpenCode automation workflow once the OpenCode setup repo is ready.
- [ ] Document post-MVP web UI scope for human review and adding tasks on the fly, using React + Express on Node.js 24 LTS.
- [X] Document optional Prometheus setup and scrape example. Completed 2026-05-23 by claude-sonnet-4-6; `docs/Prometheus.md` covers planned design, enable flag, scrape config for prometheus.taylor.lan, and security note. Implementation deferred to Scaffolding section.
- [X] Record decisions and milestones in `MEMORY.md`. Completed 2026-05-23 by claude-sonnet-4-6; current status, idempotency architecture note, session 9 run log entry added.

## In Progress

Move exactly one task here while working if multiple agents may run at the same time.

- [ ]

## Blocked

Move blocked tasks here with the blocker and the next required human action.

- [ ]

## Done

Move completed items here with a brief note.

- [X] Bootstrap project direction, workflow docs, and planning files for Agent Workbench. Completed 2026-05-22 by Codex.
