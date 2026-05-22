# Implementation Plan

High-level order of implementation. Keep this aligned with `TODO.md`.

## Discovery

- Product scope and MVP boundary confirmed: API plus CLI/scripts first; web UI later.
- Confirm exact Flask package layout.
- Inventory lessons from the `project-status` prototype.
- Inventory OpenCode automation needs from `/shared/projects/ai/opencode-setup`, using stub CLI commands first and replacing them gradually.
- Identify blockers and manual validation needs.

## Planning

- Finalize modular monolith architecture.
- Define initial API route contract.
- Define initial database schema and migration approach.
- Define `project_sections` and nullable section association for project-wide/general status records and tasks.
- Define phase tracking for status records and tasks.
- Define local/dev/stage/prod database targets, schema policy, and `APP_ENV` behavior.
- Define project type metadata and default agent selection behavior.
- Define task/status/run/review state machines.
- Define Markdown bridge strategy for context reset.

## Bootstrap MVP

Goal: get API plus CLI/scripts usable by at least one test project before building the web UI.

- Scaffold Flask backend package and dependency management.
- Add Docker Compose PostgreSQL local development service.
- Add Alembic migration baseline.
- Add environment-aware migration commands for local/dev/stage/prod, with explicit confirmation for prod.
- Implement project, project section, task, status, agent, run, event, and review schema foundations.
- Add task assignee/owner fields for agent or human responsibility.
- Add event history for task and status transitions; structured logs are acceptable as the first bootstrap shape if durable event rows are not ready yet.
- Maintain bootstrap scripts or CLI commands documented in `docs/Bootstrap-CLI.md`:
  - `task-next`
  - `task-claim`
  - `task-heartbeat`
  - `task-complete`
  - `task-block`
  - `status-show`
- Evolve bootstrap commands from local ignored state to database/API-backed behavior.
- Expand root `Makefile` for setup, validation, smoke, integration, migration, cleanup, and CLI builds.
- Add Go 1.26 CLI scaffold with build artifacts under `cli/builds/`.
- Defer web UI until API/CLI can support real project workflow validation.

## Implementation Phase: API Modules

- Implement `projects` API and service layer.
- Implement `project_sections` API and service layer.
- Implement `project_status` API and service layer, including project-wide and section-scoped status.
- Implement `project_tasks` API and service layer, including section scope, phase, leases, and idempotency.
- Implement `agents` API and service layer.
- Implement `runs` API and heartbeat model.
- Implement `events` append-only API/service model and/or bootstrap structured event logging for task/status history.
- Implement `reviews` module for cloud review findings and signoff.

## Validation Phase

- Add unit tests for state transitions and validation.
- Add API route contract tests.
- Add PostgreSQL-backed integration tests.
- Add curl smoke script for quick local feedback.
- Add Python integration-test container for richer agent workflow checks.
- Add optional Prometheus metrics smoke validation when metrics are enabled.
- Add cloud review/refactor lane before real use.

## Review

Before real use, a cloud-based AI agent should perform a larger-context review and refactor pass.

- Build a current contract map for API routes, request/response JSON, errors, scripts/CLI, database schema, Docker services, environment variables, and generated Markdown bridge files.
- Compare that contract map against docs, source, tests, Docker/Compose, README, and TODO.
- Prioritize findings by correctness, data integrity, test reliability, integration behavior, maintainability, security-sensitive assumptions, and production-readiness.
- Convert review findings into focused TODO items before broad refactoring begins.
- Refactor by module or contract boundary with validation after each change.
- Complete or explicitly defer high-risk findings before treating the project as ready for real use.

## Release

- Run full validation across API, scripts/CLI, database migrations, smoke checks, and integration tests.
- Confirm deployment target, runtime environment, PostgreSQL secrets, and network exposure with Jason.
- Use Docker Compose secrets/env files for first non-local deployments; investigate HashiCorp Vault as a later enhancement.
- Research IDP-backed authentication before exposing beyond the trusted LAN or expanding real-use scope.
- Document deployment, rollback, and recovery steps.
- Record release notes, remaining follow-up, and manual validation findings in `MEMORY.md`.
