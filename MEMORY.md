# Project Memory

Persistent project memory for `Agent Workbench`.

Agents should update this file after meaningful decisions, milestones, blockers, research findings, or implementation runs.

Keep this file concise and durable. Do not paste full chat transcripts here; store temporary transcripts under `chats/` and mirror workflow-manager logs to external storage.

## Current Status

- Current phase: planning and bootstrap.
- Last major milestone: initialized the project direction for a modular monolith, PostgreSQL-backed AI agent workbench.
- Next recommended task: confirm database target names/schema layout and API framework, then finalize the initial data model and API route contract before scaffolding backend migrations.
- Current blocker: Jason should confirm API framework, production authentication expectations, and initial deployment target preference.

## Key Decisions

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

## Architecture Notes

- Planned API namespace style: `/api/projects`, `/api/projects/{project_id}/status`, `/api/projects/{project_id}/tasks`, with aliases or convenience routes considered during contract design.
- Avoid URL versioning at first; prefer explicit compatibility policy and deprecation notes.
- Core coordination concepts: task leases, heartbeats, idempotency keys, optimistic locking, append-only events, and validation evidence.
- Potential modules: projects, project_sections, project_status, project_tasks, agents, runs, events, reviews.

## Technical Notes

- Candidate API framework: FastAPI or Flask; decide before scaffolding.
- Candidate package manager: `uv`.
- Local database: PostgreSQL container via Docker Compose.
- Target schema plan is documented in `docs/Database.md`.
- Production database: `postgresql.taylor.lan` with secrets supplied externally.
- Deployment target: Docker Compose VM first, K3s later.

## Manual Validation Findings

Record findings from real systems, live services, browser/device testing, deployment targets, or Jason's checks.

- None yet.

## Open Questions

- Should the API framework be FastAPI, Flask, or another Python framework?
- Should the initial MVP include a web UI, or API/CLI/scripts only?
- What is the production authentication model for private-network deployment?
- What are the exact dev, stage, and production database names/users?
- Should shared PostgreSQL environments use separate databases with stable schema `agent_workbench`, or separate schemas per environment?
- Should OpenCode automation interact with the workbench through CLI, API, or both during bootstrap?
- Should API URLs use nested project routes, flat convenience routes, or both?
- What section/module defaults should each project type create?

## Blockers

- None.

## Agent Run Log

Newest entries first.

### 2026-05-22 - Codex

- Task: Bootstrap docs, workflow, AGENTS instructions, and planning for Agent Workbench.
- Files changed: root docs and `docs/` planning files.
- Validation: documentation-only update; no application tests exist yet.
- Result: Established modular monolith/PostgreSQL-first direction, Markdown bootstrap bridge, OpenCode-aware workflow guardrails, cloud review/refactor lane, database environment/schema planning, and section/module plus phase tracking requirements.
- Blockers or follow-up: confirm framework and initial API/data model.
