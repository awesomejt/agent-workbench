# Project Requirements

## Purpose

`Agent Workbench` provides an API-driven coordination system for AI agents working across multiple Git-controlled projects. It tracks project metadata, status, tasks, agents, runs, leases, and events in PostgreSQL 18 (Do not use SQLite) while preserving concise Markdown handoff files for local-context-reset workflows.

## Users

- Primary users: local AI coding agents, scheduled OpenCode agents, and cloud review agents.
- Secondary users: Jason and any human operator managing projects, deployments, and review gates.

## Key Features

- Multi-project registry with Git source location, project type, environment, default agents, and workflow hints.
- Project sections/modules within each project so work can be tracked at project-wide or module/section level.
- Project status tracking for current state, module/section, phase, blockers, reason, details, and history.
- Task management with priorities, module/section association, phase, dependencies, assignee/owner, leases, claim/heartbeat/complete/block transitions, and completion evidence.
- Agent registry with capabilities, default model/agent suggestions, and runtime notes.
- Agent run tracking for attempts, heartbeats, validation commands, outputs, and outcomes.
- Append-only event history for project, task, status, review, and run transitions; initial implementations may expose this through structured logs before richer event-query APIs exist.
- Review module for cloud review findings, refactor tasks, and signoff gates.
- Bootstrap scripts or CLI commands that let agents interact with Postgres before the full web UI exists.
- CLI is a Go client (`awb`) built with Cobra and Viper. Commands cover task lifecycle (next, claim, heartbeat, complete, block), project listing, and status inspection. Config resolves from `~/.config/awb/` (preferred) or `~/.config/agent-workbench/`, with `AWB_*` env vars and `--flag` overrides taking priority. Binary installs to `~/.local/bin` or `~/bin` via `make install-cli`.
- Markdown summary/memory bridge for agent context resets, generated or manually maintained during early development.
- MVP scope is API plus CLI/scripts so at least one test project can use the workbench before the web UI is built.
- Web UI follows MVP and should focus on human review plus adding/editing tasks on the fly.
- Post-MVP web UI target stack is React, Node.js 24 LTS, latest npm, and Express.
- Local Docker Compose PostgreSQL for development and tests.
- Environment-driven database configuration for local, dev, stage, and production.
- Explicit environment selection through `APP_ENV=local|dev|stage|prod` and optional `--env` flags in CLI/scripts.
- Configurable local project discovery roots, defaulting to `~/projects/ai`, `~/projects/courses`, `~/projects/dev`, and `~/projects/infra`.
- Optional Prometheus metrics endpoint for API health, task claims, run outcomes, and queue depth.
- Runtime agent metrics captured per run: `model_id`, `prompt_tokens`, `completion_tokens`, `latency_ms`, and `prompt_category` — stored on the `runs` table to inform lease duration tuning and model selection heuristics.

## API Shape

See `docs/API-Contracts.md` for the current canonical planning contract. This section is a summary only.

Prefer stable resource names over URL versioning for the first release. Initial route style should be decided during contract planning, with likely routes such as:

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `GET /api/projects/{project_id}/sections`
- `POST /api/projects/{project_id}/sections`
- `GET /api/projects/{project_id}/status`
- `PATCH /api/projects/{project_id}/status`
- `GET /api/projects/{project_id}/tasks`
- `POST /api/projects/{project_id}/tasks`
- `POST /api/tasks/{task_id}/claim`
- `POST /api/tasks/{task_id}/heartbeat`
- `POST /api/tasks/{task_id}/complete`
- `POST /api/tasks/{task_id}/block`
- `GET /api/agents`
- `POST /api/runs`
- `POST /api/events`

Convenience routes such as `/api/project/status` can be considered for current-project contexts, but canonical multi-project routes should include project identity.

## Core Data Concepts

- `project`: named Git-controlled work item with type, source URL/path, environment, default agent, and metadata.
- `project_section`: optional module/section inside a project, such as API, web, CLI, chapter, lesson, article section, or infrastructure area.
- `project_status`: current state and status history for a project, optionally scoped to a `project_section`, and always associated with a phase.
- `task`: actionable work item with status, priority, phase, optional `project_section`, dependencies, assignee/owner, claim lease, and validation expectations.
- `agent`: named automation or model profile with capabilities and defaults.
- `run`: one agent execution attempt with task/project linkage, heartbeat, logs, validation, and result.
- `event`: append-only audit record for important transitions and notes.
- `review`: cloud/human review finding, severity, status, and signoff state.

## Section And Phase Rules

- A project can contain zero or more sections/modules.
- Status records and tasks may reference a section/module.
- If a status record or task has no `project_section_id`, it is project-wide/general work.
- Do not require a magic `general` section row for project-wide work; UI/CLI may display null section as `Project-wide` or `General`.
- Supported initial phases: `planning`, `research`, `implementation`, `testing`, and `review`.
- Phase should be tracked on both status records and tasks.
- Project types may define default sections and default phase workflows.

## Non-Functional Requirements

- Performance: support many projects and multiple simultaneous agents without task duplication.
- Security: private-network MVP may run without authentication; secrets must stay out of Git; database URLs and credentials are environment-injected.
- Reliability: task claims and status transitions must be atomic and recoverable after agent failure.
- Auditability: meaningful state transitions should create durable events or structured log entries during the bootstrap phase.
- Observability: Prometheus support should be optional, disabled by default or explicitly configured, and simple to enable for `prometheus.taylor.lan`.
- Compatibility: local development uses Docker Compose PostgreSQL; production may use Docker Compose VM or K3s.
- Agent ergonomics: command outputs should be concise, machine-readable when needed, and useful after context reset.
- Maintainability: modules should be internally cohesive but deployed as one modular monolith initially.

## Out Of Scope

- Public multi-tenant SaaS behavior in MVP.
- Web UI in MVP; API and CLI/scripts come first.
- Authentication/authorization in MVP for trusted local-network use; IDP research is a future work item.
- Replacing Git as source control.
- Committing production secrets or raw long-form transcripts.
- Building many independently deployed microservices at the start.

## Acceptance Criteria

- A local agent can discover, claim, update, and complete tasks through API/CLI without editing Markdown as the primary state store.
- PostgreSQL stores projects, sections/modules, status records, tasks, agents, runs, and events with migrations.
- Local, dev, stage, and prod database targets can run the same schema/migrations, with prod expected on `postgresql.taylor.lan`.
- Multiple agents can safely attempt work without claiming the same task concurrently, and each task can show its current assignee/owner.
- Project types can influence default sections/modules, default phases, default agents, and workflow hints.
- Local dev can run with a PostgreSQL container.
- Dev/stage/production database URLs can be configured without code changes or committed secrets.
- Markdown context files can still summarize current state for local agent loops.
- Smoke and integration validation exist before real use.
- Optional Prometheus metrics can be enabled and scraped by the homelab Prometheus server.
- Cloud review/refactor is completed or explicitly deferred before production deployment.
