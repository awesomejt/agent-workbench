# Project Memory

Persistent project memory for `Agent Workbench`.

Agents should update this file after meaningful decisions, milestones, blockers, research findings, or implementation runs.

Keep this file concise and durable. Do not paste full chat transcripts here; store session logs under `.agents/chat/` (gitignored, local-only) and formal review outputs under `docs/reviews/` (committed).

## Current Status

- Current phase: dogfood — API/CLI MVP is live enough for self-coordination, with follow-up review findings recorded.
- Latest review milestone (2026-05-25 Codex): formal project review recorded in `docs/reviews/2026-05-25-1632-codex-project-review.md`. Main risks: `awb --project` flag handling, masked smoke failures, direct claim bypass of `blocks` dependencies, project phase high-water drift, invalid default `project_type`, section/review validation gaps, and docs contract drift.
- Validation snapshot (2026-05-25 Codex): `make validate`, `make test` (211 passed), `make cli-vet`, `make build-cli`, `make cli-test`, `make cli-clean-build-check`, and `npm run build` passed. `make smoke` reported 1 failing smoke check but exited successfully because the Makefile target masks smoke script failures.
- Dogfood transition complete: `awb` is the primary task source; `TODO.md` is read-only reference.
- Queue snapshot (2026-05-25 Codex): `awb task list --available` for `agent-workbench` returned no available tasks.
- Current blocker: non-local database credential/user details still require human confirmation before dev/stage/prod migration/deployment.

## Key Decisions

- MVP scope is API plus CLI/scripts first; web UI is post-MVP for human review and adding tasks on the fly.
- CI runs on a self-hosted GitHub Actions runner (host needs Docker only); all build tools run in purpose-built containers pulled from Harbor.
- Harbor projects: `proxy/` (pull-through cache for DockerHub/ghcr.io), `base/` (curated base images), `ci/` (CI tool images). CI images live in a separate `infra/homelab-images` repo alongside Ansible.
- CI image tag convention: `<upstream-version>-<build-revision>` (e.g. `python-uv:3.14-1`); revision increments for any image change without an upstream version bump, resets to `-1` on upstream version bump. Follows Debian package versioning. Avoid `:latest` in CI workflows.
- CI jobs are purpose-driven (separate python-uv, golang, node images) rather than a single fat image.
- Private-network/local homelab MVP can defer authentication; research IDP-backed auth before broader exposure.
- First non-local deployment should use Docker Compose env files or Compose secrets; HashiCorp Vault is future research.
- Tasks need assignee/owner information for the responsible agent or human.
- Status and task changes need event history; structured logs are acceptable as an initial bootstrap mechanism.
- Prometheus support should be optional and easy to enable; Jason's server is `prometheus.taylor.lan`.
- Use a modular monolith before considering separate services.
- Runtime agent metrics (model_id, token counts, latency_ms, prompt_category) belong on the `runs` table in agent-workbench — used to inform future lease duration tuning and model selection.
- Dogfood gate: all Codex P0–P2 pre-dogfood fixes must be completed before registering agent-workbench as its own project and switching from TODO.md edits to `awb task claim/complete` for remaining work.
- Codex full-repo review (2026-05-22) accepted as the cloud review gate. Key validated findings: `cli/internal/output/` silently git-ignored (clean clone fails), ruff format fails 15 files, mypy fails 17 errors, `awb task next` not lease-aware, task transitions don't auto-append events, root `.env.example.local` uses wrong port (5432 vs 5433).
- A separate `benchmark-harness` project will handle structured evaluation: prompt libraries, scoring rubrics, comparison reports. It will consume agent-workbench as infrastructure but live independently.
- PostgreSQL should become the preferred source of truth for project/task/status/agent/run state.
- Git remains the source of truth for source code and migrations.
- Markdown files remain useful as a context bridge while OpenCode/local agent iterations reset context.
- Start with local PostgreSQL in Docker Compose; dev/stage/production databases use environment-injected URLs.
- Use `APP_ENV=local|dev|stage|prod` and optional CLI/script `--env` flags to select database targets.
- Deployed runtime should default to `prod` once real use begins; local commands must explicitly select `local`.
- Production PostgreSQL host is expected to be `postgresql.taylor.lan`; secrets stay outside Git.
- Existing local project roots are `~/projects/ai`, `~/projects/courses`, `~/projects/dev`, and `~/projects/infra`; Ansible lives at `~/projects/infra/ansible`.
- Support multiple project types with default sections/modules, phases, default agent choices, and workflow hints.
- Status records and tasks should both track phase and optional `project_section_id`; null section means project-wide/general work.
- Add cloud review/refactor before real use.
- Accepted Grok review recommendations: centralize API contracts in `docs/API-Contracts.md`, add human-readable diagrams, clarify bootstrap CLI transition phases, and weight task selection toward high-impact API/CLI MVP unblockers.
- Deferred Grok review recommendations: separate `CHANGELOG.md` and heavy web/ops/auth work are unnecessary before API/CLI scaffolding; `MEMORY.md` remains the lightweight decision log for now.
- Project boundary clarified: active work is in `agent-workbench`; `/shared/projects/dev/project-status` is a prototype/reference source only. If future context points at mixed projects, agents should ask before editing.

## Scaffolding Decisions (2026-05-22)

- Flask package layout: `src/` layout inside `api/`, application factory `create_app()` in `app.py`, Flask-SQLAlchemy 3.x, pydantic-settings for typed config that fails fast on missing `DATABASE_URL`.
- Repository structure: `api/` (Python/Flask), `cli/` (Go, stub), `web/` (React, stub) as top-level component dirs; `compose.yaml` and `Makefile` at root to orchestrate all three.
- Alembic configuration: `api/alembic.ini` with semantic revision IDs (`YYYYMMDD_<rev>_<slug>`); `env.py` reads `APP_ENV` and resolves the matching `AGENT_WORKBENCH_*_DATABASE_URL`; creates schema and pgcrypto extension if absent.
- Docker Compose workflow: `db` service always available; `api` and `migrations` services behind profiles (`--profile api`, `--profile migrate`) to avoid accidental startup.
- Primary local dev workflow: Docker Compose for db and migrations; `uv` commands run inside `api/` for lint/test/type-check via Makefile targets.
- Bootstrap scripts remain at `scripts/` (root level) as interim tools until Go CLI replaces them.
- Version policy: target major.minor versions; patch versions managed automatically by uv/go modules/npm; no manual patch pinning.

## Architecture Notes

- API namespace style: canonical multi-project routes `/api/projects`, `/api/projects/{project_id}/status`, `/api/projects/{project_id}/tasks`; explicit action routes for atomic transitions (e.g., `/api/tasks/{task_id}/claim`).
- No URL versioning for MVP; document compatibility and deprecation when routes change.
- Core coordination concepts: task leases, heartbeats, idempotency keys, optimistic locking (`version` field), append-only events, and validation evidence.
- Implemented modules (as of 2026-05-22 scaffolding): `projects`, `project_sections`, `project_status`, `tasks`, `agents`, `runs`, `events`, `reviews` — each with SQLAlchemy models, Blueprint stub, and service stub.
- All models use `Uuid` PKs, `DateTime(timezone=True)`, `version` int for optimistic locking; `MetaData(schema="agent_workbench")` applied globally.
- Tasks have lease fields: `claimed_by`, `claimed_until`, `lease_version`. The old `tasks.idempotency_key` column was removed and replaced by a proper `idempotency_keys` table (migration c8e1f2a3b4d5).
- `idempotency_keys` table: unique on `(idempotency_key, endpoint, actor_name)`; 24-hour TTL checked on read; stores `response_status` + `response_body` for replay. Idempotency-Key HTTP header triggers check/store on task claim/heartbeat/complete/block.
- Events table is append-only by design; no `updated_at` column.

## Technical Notes

- API: Flask 3.x, Flask-SQLAlchemy 3.x (SQLAlchemy 2.x), Alembic 1.x, psycopg 3.x, pydantic-settings 2.x; Python 3.14; `uv` package manager.
- Package location: `api/src/agent_workbench/`; entry point `agent-workbench-api = "agent_workbench.app:main"`.
- Local database: PostgreSQL 18 container via `docker compose up -d db`; schema `agent_workbench` created by Alembic `env.py` on first migration run. Local host port is **5433** (not 5432, which is taken by project-status-db).
- Docker Compose volume mount: PostgreSQL 18 uses `/var/lib/postgresql` (not `/data` subdirectory — required for pg18+).
- `make migrate` / `make migrate-generate` use `uv run --env-file .env alembic ...`; `DATABASE_URL` in `api/.env` (gitignored).
- SQLAlchemy 2.x: `lazy="dynamic"` removed; all back-reference relationships use `lazy="select"` instead.
- Test database: `agent_workbench_test`; conftest fixtures run Alembic migrations once per session, truncate tables after each test via `TRUNCATE ... CASCADE`.
- Alembic `include_name` filter in `env.py` scopes autogenerate to `agent_workbench` schema only; prevents spurious `drop_table('alembic_version')` in migrations.
- Database servers: local container, `postgresql-dev`, `postgresql-stage`, `postgresql`/`postgresql.taylor.lan` for prod.
- Production database: `postgresql`/`postgresql.taylor.lan` with secrets supplied externally; never committed.
- Deployment target: Docker Compose VM first; K3s is future work.
- CLI direction: Go 1.26, Cobra + Viper, binary `awb` built to `cli/builds/` (git-ignored). Module path `agent-workbench/cli` (local; update when GitHub remote is added). Config resolution: `--flag` > `AWB_*` env var > `~/.config/awb/config.*` > `~/.config/agent-workbench/config.*`; yaml, json, and toml formats all supported. Install via `make install-cli` or `scripts/install-awb.sh` (targets `~/.local/bin`, then `~/bin`).
- Bootstrap scripts: `scripts/` (root level), backed by `.agent-workbench/bootstrap-state.json` (git-ignored), used until Go CLI replaces them.

## Manual Validation Findings

Record findings from real systems, live services, browser/device testing, deployment targets, or Jason's checks.

- None yet.

## Open Questions

- Which IDP/auth model should be used after the private-network MVP? (task `1977b02a`)
- What are the exact dev, stage, and production database names/users? (task `0f1079ef` — needs Jason's decision)
- What are the exact dev/stage/prod credential injection details for the first Docker Compose VM deployment?
- Should OpenCode automation interact with the workbench through CLI, API, or both during bootstrap?
- **Resolved:** Section/module defaults per project type — documented in `docs/Project-Types.md`.
- **Resolved:** Flat convenience routes — not for MVP; canonical multi-project routes only.
- **Resolved:** OpenAPI strategy — `docs/API-Contracts.md` is canonical through MVP; `flask-smorest` post-MVP.

## Blockers

- None.

## Agent Run Log

Newest entries first.

### 2026-05-26 - claude-sonnet-4-6

- Task: Extend onboarding system with project creation, archive pass, server install, and documentation.
- Files changed: `scripts/onboard.py` (type: project/task two-pass processing, --archive flag), `onboarding/task.template.md` (add type: task field), `onboarding/project.template.md` (new), `scripts/install-onboard.sh` (new; writes awb-onboard + awb-onboard-archive stubs, no system path assumptions), `docs/Onboarding.md` (new; full reference with Mermaid lifecycle/flow/deploy diagrams), `README.md` (updated onboarding section), `Makefile` (onboard-archive + install-onboard targets).
- Validation: `python3 -c "import ast; ast.parse(...)"` clean; dry-run smoke test of both passes confirmed correct output; `make onboard-archive ONBOARD_DRY_RUN=1` passed.
- Result: Onboarding now supports two file types. A project file and its task files can be dropped together — projects are registered first, tasks second. Processed files are archived by a separate nightly pass. Server/container deployments use `install-onboard.sh` with explicit flags; no path assumptions from the build host.
- Blockers or follow-up: None.

### 2026-05-25 - Codex

- Task: Review the project so far and record findings in `docs/reviews/`.
- Files changed: `docs/reviews/2026-05-25-1632-codex-project-review.md`, `MEMORY.md`, `.agents/chat/2026-05-25-1632-codex-project-review.md`.
- Validation: `make validate` passed; `make test` passed with 211 tests; `make cli-vet`, `make build-cli`, `make cli-test`, `make cli-clean-build-check`, and `npm run build` passed. `make smoke` reported 5 passed / 1 failed but exited successfully because the Makefile target masks failures.
- Result: Formal review recorded. Highest-risk findings are broken `awb --project` handling, false-green smoke target, direct claim bypass of `blocks`, phase high-water drift, and invalid default project type.
- Blockers or follow-up: Create focused workbench tasks for the review findings once task creation workflow is chosen.

### 2026-05-23 - claude-sonnet-4-6 (session 10)

- Task: Review task queue, close already-complete tasks, then complete design work.
- Files changed: `docs/API-Contracts.md` (contract strategy + in-code API docs sections, resolved open questions), `docs/State-Machines.md` (new; task/phase/run/review state machines + assignment vs. claiming model), `docs/Project-Types.md` (new; 6-type vocab, default sections, phase expectations, agent role defaults), `docs/Task-Duration.md` (new; t-shirt sizing, lease resolution, multipliers), `api/src/agent_workbench/projects/routes.py` (_VALID_PROJECT_TYPES validation), `api/src/agent_workbench/projects/models.py` (default `code`), `api/tests/test_projects.py` (3 new tests), `AGENTS.md` (Markdown File Strategy section), `MEMORY.md` (this update).
- Validation: 189 tests pass; ruff clean.
- Closed tasks: cee07b4f (idempotency behavior), ed225a08 (claim/lease behavior), 2748e2cc (event model), 43b6421d (PG container), 34c3fb2e (Prometheus scope), 700d45cb (event history strategy), 264cb3f7 (OpenAPI decision), a3e64fe6 (in-code API docs), 1fe5ebe8 (state machines), ed2fe9f6 (project types), e1efdd78 (assignee/owner model), f8e61d04 (task duration), 3fea7a50 (Markdown strategy).
- Result: 13 tasks closed in one session. Design queue largely complete. Remaining open work is mostly human-decision items, post-MVP features, and implementation tasks.
- Blockers or follow-up: Jason needs to confirm dev/stage/prod DB names/users (task 0f1079ef).

### 2026-05-23 - claude-sonnet-4-6 (session 9)

- Task: Commit pending docs work, then execute P2 idempotency + Tests & Quality + Cloud review signoff + Documentation stubs in order.
- Files changed: `README.md` (rewrite), `docs/Development.md` (new), `scripts/seed_dev.py` (new), `Makefile` (seed-dev target), `TODO.md` (sync); then `api/src/agent_workbench/idempotency/` (new module + model + service), `api/migrations/versions/20260523_c8e1f2a3b4d5_add_idempotency_keys_table.py`, `tasks/models.py` (drop idempotency_key field), `tasks/service.py` (drop idempotency_key param), `tasks/routes.py` (check/store idempotency on 4 endpoints), `cli/internal/api/client.go` (doWithHeaders, updated 4 task methods), `cli/cmd/root.go` (newIdempotencyKey), `cli/cmd/task_{claim,heartbeat,complete,block}.go`; then `tests/test_idempotency.py` (7 tests), `tests/test_tasks.py` (+9 state machine + available filter tests), `tests/conftest.py` (add idempotency_keys to truncate list); then `docs/Secrets.md` (new), `docs/Prometheus.md` (new), `MEMORY.md` (this update).
- Validation: 101 tests pass; `make validate` (ruff + mypy) passes; `make cli-vet` passes; `make build-cli` succeeds.
- Result: All 4 planned work areas complete. P2 idempotency properly scoped to endpoint+actor+key table. Cloud review signoff formally done — all 3 highest-risk Codex items resolved. 46 open tasks remain.
- Blockers or follow-up: Jason still needs to confirm dev/stage/prod DB names/users and secret injection details.

### 2026-05-23 - claude-sonnet-4-6 (session 8)

- Task: Codex review triage, pre-dogfood planning, CLI install improvements, doc updates.
- Files changed: `cli/cmd/root.go` (fix `$HOME` expansion, `~/.config/awb` config path, yaml/json/toml support), `scripts/install-awb.sh` (new), `Makefile` (`install-cli`), `TODO.md` (Review section done, pre-dogfood fix list, dogfood item), `MEMORY.md`, `status.yaml`, all 5 docs in `docs/`.
- Validation: `go vet ./...` clean; `make build-cli` succeeds.
- Result: Codex review accepted as cloud review gate; 20 pre-dogfood fix items triaged into P0–P3; dogfood intent documented. All project docs updated to reflect CLI as shipped.
- Blockers or follow-up: P0 fixes next (rename `cli/internal/output` → `render`, nil deref, double-error print, api-url trailing slash).

### 2026-05-22 - claude-sonnet-4-6 (session 7)

- Task: CLI install script and config path improvements.
- Files changed: `cli/cmd/root.go` (fix `$HOME` expansion bug, add `~/.config/awb` as first config path, drop `SetConfigType` to support yaml/json/toml), `scripts/install-awb.sh` (new; installs to `~/.local/bin` or `~/bin`, auto-builds if binary absent, warns when dir not on PATH), `Makefile` (`install-cli` target added, help text updated).
- Validation: `go vet ./...` clean; `make build-cli` succeeds; install script syntax-checked.
- Result: `awb` can now be installed with `make install-cli`. Config files in `~/.config/awb/` take priority over `~/.config/agent-workbench/`; both yaml and json are supported.
- Blockers or follow-up: cloud review gate is the next priority.

### 2026-05-22 - claude-sonnet-4-6 (session 5)

- Task: Grok review triage + task lease duration + two Grok security fixes.
- Files changed: `api/src/agent_workbench/tasks/models.py` (add `estimated_duration_seconds`), `tasks/service.py` (DEFAULT_LEASE_SECONDS=1800, use task estimate as fallback), `tasks/routes.py` (3-level duration resolution), `api/migrations/versions/20260522_a1b2c3d4e5f6_*` (ADD COLUMN migration), `api/tests/test_tasks.py` (4 new duration tests), `api/src/agent_workbench/config.py` (secret_key prod validator), `api/src/agent_workbench/app.py` (/health DB ping, 503 on failure), `TODO.md` (t-shirt sizing future item).
- Validation: 54 tests, 54 passed, 0.89s; `make lint` clean.
- Result: Task leases now use a 3-level duration resolution (request > task estimate > 1800s system default). Prod secret_key default is rejected at startup. /health returns db status and 503 when DB is unreachable. Confirmed Flask over FastAPI; kept agent_workbench namespace. Committed two fixes separately: feat(tasks) and fix(api).
- Blockers or follow-up: next task is Go CLI scaffold (Cobra + Viper, cli/builds/); cloud review gate before real use.

### 2026-05-22 - claude-sonnet-4-6 (session 4)

- Task: API contract tests for agents, projects, and tasks modules.
- Files changed: `api/tests/test_agents.py`, `api/tests/test_projects.py`, `api/tests/test_tasks.py`; `api/tests/conftest.py` (fixed Flask-SQLAlchemy 3.x session scoping hang).
- Validation: 50 tests, 50 passed, 0.83s; `make lint` clean.
- Result: Full CRUD + optimistic locking tests for agents and projects; task lease lifecycle tests (claim, heartbeat, complete, block). Fixed critical conftest bug: FSA 3.x scopes session to app context, not per-request — caused idle-in-transaction deadlock on TRUNCATE. Fix: rollback+remove session in outer context, use engine.connect() for TRUNCATE, run cleanup BEFORE each test.
- Blockers or follow-up: next task is Go CLI scaffold; cloud review gate before real use.

### 2026-05-22 - claude-sonnet-4-6 (session 3)

- Task: First Alembic migration, pytest fixtures, curl smoke checks.
- Files changed: `docker-compose.yml` (port 5433, pg18 volume mount), `api/.env.example`, `api/migrations/env.py` (include_name schema filter), `api/migrations/versions/20260522_eb91537942a2_initial_schema.py`, `api/src/agent_workbench/projects/models.py` + `tasks/models.py` + `runs/models.py` (lazy="select"), `api/tests/conftest.py`, `api/tests/test_health.py`, `scripts/smoke-curl.sh`, `Makefile` (migrate/migrate-generate/test targets use --env-file .env), `TODO.md`, `MEMORY.md`, `status.yaml`.
- Validation: `make lint` clean, `make test` 1 passed, `make smoke` 6/6 passed.
- Result: Local PostgreSQL 18 running on port 5433. Initial schema (8 tables) applied via Alembic. pytest session fixture runs migrations against agent_workbench_test; autouse clean_db truncates after each test. Smoke script validates health, projects, agents, events endpoints.
- Blockers or follow-up: dev/stage/prod database names/users still unconfirmed; next task is API contract tests for core modules.

### 2026-05-22 - claude-sonnet-4-6 (session 2)

- Task: Implement all 8 core API modules after context compaction; close planning tasks L61-L63; clean up .claude/settings.json allow rules.
- Files changed: `api/src/agent_workbench/projects/`, `project_sections/`, `project_status/`, `tasks/`, `agents/`, `runs/`, `events/`, `reviews/` (routes + service for each); `TODO.md`, `MEMORY.md`, `status.yaml`, `.claude/settings.json`.
- Validation: `make lint` clean, `make validate` passes imports.
- Result: All 8 modules have working route + service implementations. Tasks module has atomic lease coordination (targeted UPDATE, rowcount check). Events module is append-only. Runs module has heartbeat/complete/fail state transitions. Reviewed/explained Claude Code settings file priority (user > project-local > project > enterprise).
- Blockers or follow-up: First Alembic migration needs DB up; pytest setup with PostgreSQL fixture is the next unlocked task; dev/stage/prod database names/users still unconfirmed.

### 2026-05-22 - claude-sonnet-4-6

- Task: Scaffold Flask API backend, Docker Compose, Alembic, and repo structure.
- Files changed: `api/` directory (entire tree), `cli/.gitkeep`, `web/.gitkeep`, `docker-compose.yml`, `Dockerfile` (moved to `api/`), `Makefile` (full rewrite), `docs/Tech-Stack.md`, `TODO.md`, `MEMORY.md`, `status.yaml`.
- Validation: `make validate` passed, `make lint` clean (ruff), all 8 domain model imports verified.
- Result: `api/src/agent_workbench/` package with application factory, pydantic-settings config, Flask-SQLAlchemy DB, 8 domain modules (models + blueprint + service stubs), Alembic configured for schema-aware migrations with APP_ENV-driven URL selection. Monorepo split into `api/`/`cli/`/`web/` per Jason's direction.
- Blockers or follow-up: confirm dev/stage/prod DB names/users before running non-local migrations; next step is implementing core API modules (projects, tasks).

### 2026-05-22 - Codex

- Task: Record project-boundary clarification after mixed `project-status`/`agent-workbench` context.
- Files changed: `AGENTS.md`, `MEMORY.md`, `status.yaml`.
- Validation: pending final validation before commit.
- Result: Made `agent-workbench` the explicit default work target and documented `project-status` as reference material only.
- Blockers or follow-up: none.

### 2026-05-22 - Codex

- Task: Evaluate Grok's planning/scaffolding review and apply recommendations with merit.
- Files changed: `docs/API-Contracts.md`, `docs/Architecture.md`, `docs/Bootstrap-CLI.md`, `docs/Requirements.md`, `docs/Implementation.md`, `AGENT_WORKFLOW.md`, `TODO.md`, `MEMORY.md`, `status.yaml`.
- Validation: `make validate` passed; `git diff --check` passed.
- Result: Accepted the review's strongest low-risk recommendations: centralized API contract planning, added Mermaid ERD and task-claim sequence diagrams, documented bootstrap transition phases, and made task selection explicitly favor high-impact MVP unblockers. Deferred a separate changelog and heavier post-MVP scope.
- Blockers or follow-up: Jason still needs to confirm non-local database names/users and secret injection details; next engineering task remains Flask package/backend scaffolding.

### 2026-05-22 - Codex

- Task: Record MVP, auth, secrets, ownership, event history, and Prometheus planning decisions.
- Files changed: planning docs, TODO, MEMORY, and status.
- Validation: documentation-only update.
- Result: Clarified API/CLI MVP, post-MVP web UI, deferred auth/IDP research, Compose-first secrets with Vault later, task assignee/owner requirement, event-history/logging requirement, and optional Prometheus support.
- Blockers or follow-up: confirm exact dev/stage/prod database names/users and secret injection details before non-local deployment.

### 2026-05-22 - Codex

- Task: Add bootstrap commands for OpenCode handoff.
- Files changed: `scripts/`, `docs/Bootstrap-CLI.md`, `Makefile`, README, TODO, MEMORY, and `.gitignore`.
- Validation: `make validate`, `./scripts/status-show --json`, and `./scripts/task-next --json` passed.
- Result: Added local-state-backed command stubs for task next, claim, heartbeat, complete, block, and status show.
- Blockers or follow-up: add scheduled OpenCode wrapper and later replace stubs with database/API-backed CLI.

### 2026-05-22 - Codex

- Task: Record stack, deployment, database, OpenCode, and CLI build decisions.
- Files changed: planning docs, TODO, MEMORY, README, status.
- Validation: documentation-only update.
- Result: Documented Python 3.14 plus Flask APIs, stub CLI bootstrap for OpenCode, Docker Compose VM deployment first, separate database servers with stable schema, and Go 1.26 CLI build output under `cli/builds/`.
- Blockers or follow-up: add stub CLI commands and decide Flask package layout.

### 2026-05-22 - Codex

- Task: Bootstrap docs, workflow, AGENTS instructions, and planning for Agent Workbench.
- Files changed: root docs and `docs/` planning files.
- Validation: documentation-only update; no application tests exist yet.
- Result: Established modular monolith/PostgreSQL-first direction, Markdown bootstrap bridge, OpenCode-aware workflow guardrails, cloud review/refactor lane, database environment/schema planning, and section/module plus phase tracking requirements.
- Blockers or follow-up: confirm framework and initial API/data model.
