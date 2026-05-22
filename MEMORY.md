# Project Memory

Persistent project memory for `Agent Workbench`.

Agents should update this file after meaningful decisions, milestones, blockers, research findings, or implementation runs.

Keep this file concise and durable. Do not paste full chat transcripts here; store temporary transcripts under `chats/` and mirror workflow-manager logs to external storage.

## Current Status

- Current phase: planning and bootstrap.
- Last major milestone: incorporated multi-AI planning review by adding a canonical API contract guide, Mermaid data/claim diagrams, and bootstrap transition roadmap.
- Next recommended task: decide Flask package layout, then scaffold the backend/API and Alembic migration foundation against the documented contracts.
- Current blocker: Jason should confirm exact dev/stage/prod database names/users and the first non-local deployment secret injection details.

## Key Decisions

- MVP scope is API plus CLI/scripts first; web UI is post-MVP for human review and adding tasks on the fly.
- Private-network/local homelab MVP can defer authentication; research IDP-backed auth before broader exposure.
- First non-local deployment should use Docker Compose env files or Compose secrets; HashiCorp Vault is future research.
- Tasks need assignee/owner information for the responsible agent or human.
- Status and task changes need event history; structured logs are acceptable as an initial bootstrap mechanism.
- Prometheus support should be optional and easy to enable; Jason's server is `prometheus.taylor.lan`.
- Use a modular monolith before considering separate services.
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

## Architecture Notes

- Planned API namespace style: `/api/projects`, `/api/projects/{project_id}/status`, `/api/projects/{project_id}/tasks`, with aliases or convenience routes considered during contract design.
- Avoid URL versioning at first; prefer explicit compatibility policy and deprecation notes.
- Core coordination concepts: task leases, heartbeats, idempotency keys, optimistic locking, append-only events, and validation evidence.
- Potential modules: projects, project_sections, project_status, project_tasks, agents, runs, events, reviews.

## Technical Notes

- API framework: Flask.
- API runtime: Python 3.14 latest.
- Package manager: `uv`.
- Local database: PostgreSQL container via Docker Compose.
- Target schema plan is documented in `docs/Database.md`.
- Database servers: local container, `postgresql-dev`, `postgresql-stage`, and `postgresql`/`postgresql.taylor.lan` for prod.
- Production database: `postgresql`/`postgresql.taylor.lan` with secrets supplied externally.
- Deployment target: Docker Compose VM first; K3s is future work.
- CLI direction: Go 1.26 managed by Makefile, with build artifacts under `cli/builds/` excluded from Git.
- OpenCode direction: use stub CLI commands first, then gradually replace with real CLI/API-backed behavior. Current stubs live under `scripts/` and use ignored `.agent-workbench/bootstrap-state.json`.

## Manual Validation Findings

Record findings from real systems, live services, browser/device testing, deployment targets, or Jason's checks.

- None yet.

## Open Questions

- Which IDP/auth model should be used after the private-network MVP?
- What are the exact dev, stage, and production database names/users?
- What are the exact dev/stage/prod credential injection details for the first Docker Compose VM deployment?
- Should OpenCode automation interact with the workbench through CLI, API, or both during bootstrap?
- Should API URLs use nested project routes, flat convenience routes, or both?
- What section/module defaults should each project type create?

## Blockers

- None.

## Agent Run Log

Newest entries first.

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
