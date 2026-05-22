# Project TODO

Task list for `Agent Workbench`, organized by ownership and project phase.

## Needs Attention

Items here require Jason's input, a decision, credentials, external access, or manual validation before agent work can continue.

- [ ] Confirm API framework: FastAPI, Flask, or another Python framework.
- [ ] Confirm whether MVP includes web UI or starts with API plus CLI/scripts.
- [ ] Confirm production authentication and network exposure expectations.
- [ ] Confirm dev/stage/production database names, users, schema layout, and secret injection approach.
- [ ] Confirm whether OpenCode scheduled runs should use CLI, API, or both during bootstrap.
- [ ] Confirm whether deployed runtime should default to `APP_ENV=prod` while local/test commands explicitly select `APP_ENV=local`.
- [ ] Confirm whether shared PostgreSQL environments should use separate databases with schema `agent_workbench` or separate schemas per environment.
- [ ] Confirm deployment target order: Docker Compose VM first, K3s later.

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
- [ ] Inventory reusable lessons from `/shared/projects/dev/project-status` without copying known implementation drift.
- [ ] Inventory OpenCode setup repo requirements from `/shared/projects/ai/opencode-setup`.
- [ ] Decide initial API framework and package layout.
- [ ] Define initial module boundaries: projects, project_sections, status, tasks, agents, runs, events, reviews.
- [ ] Define initial API route style and compatibility policy without URL versioning by default.
- [ ] Define initial database schema and migration strategy.
- [ ] Define local/dev/stage/prod database target names and stable schema policy in `docs/Database.md`.
- [ ] Define project discovery config for `~/projects/ai`, `~/projects/courses`, `~/projects/dev`, and `~/projects/infra`.
- [ ] Define project type vocabulary, default sections/modules, phase workflows, and default agent selection rules.
- [ ] Define state machines for project status, task status, agent run status, and review findings.
- [ ] Define bootstrap transition from Markdown files to Postgres-backed scripts/CLI/API.

### Architecture And Contracts

- [ ] Draft API route contract for project info, project sections/modules, project status, project tasks, agents, runs, and events.
- [ ] Draft database ERD or schema notes for projects, project_sections, status records, tasks, task events, agents, runs, leases, and reviews.
- [ ] Define nullable `project_section_id` behavior for project-wide/general status records and tasks.
- [ ] Define phase enum and validation behavior for status records and tasks.
- [ ] Define optimistic locking/version fields for mutable resources.
- [ ] Define idempotency key behavior for agent-submitted commands.
- [ ] Define task claim/lease/heartbeat behavior.
- [ ] Define append-only event model and retention expectations.
- [ ] Define Markdown summary/mirroring strategy for `MEMORY.md`, `TODO.md`, and project status snapshots.
- [X] Define local/dev/stage/prod environment variable names in `docs/Database.md`. Completed 2026-05-22 by Codex.
- [ ] Add example environment files for local, dev, stage, and prod without secrets.

### Scaffolding

- [ ] Add backend project structure after framework decision.
- [ ] Add Docker Compose with local PostgreSQL container.
- [ ] Add example env files without secrets.
- [ ] Add database migration tooling.
- [ ] Add migration commands that require explicit `APP_ENV` for dev/stage/prod targets.
- [X] Add safe database bootstrap docs and SQL template for creating target schemas without embedding secrets. Completed 2026-05-22 by Codex.
- [ ] Add environment-aware wrapper command for running schema bootstrap against local/dev/stage/prod.
- [ ] Add root `Makefile` with setup, lint, test, smoke, integration-test, migration, and cleanup targets.
- [ ] Add curl smoke checks for API health and basic workflow validation.
- [ ] Add Python containerized integration-test runner.
- [ ] Add scripts or CLI bootstrap commands for task next/claim/complete/block/status.

### Implementation Phase: Core API Modules

- [ ] Implement `projects` module for project metadata, Git source location, type, environment, and defaults.
- [ ] Implement `project_sections` module for modules/sections within a project.
- [ ] Implement `project_status` module for project-wide and section-scoped current status and history.
- [ ] Implement `project_tasks` module for project-wide and section-scoped tasks, priorities, phases, dependencies, leases, and completion evidence.
- [ ] Implement `agents` module for agent registry, capabilities, defaults, and runtime hints.
- [ ] Implement `runs` module for run attempts, heartbeats, validation, and outcomes.
- [ ] Implement `events` module as append-only audit trail.
- [ ] Implement `reviews` module for cloud review findings and signoff gates.

### Tests And Quality

- [ ] Add unit tests for state transitions and validation.
- [ ] Add API tests for all module contracts.
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
- [ ] Document secret handling and Ansible integration expectations without copying secrets.
- [ ] Document OpenCode automation workflow once the OpenCode setup repo is ready.
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
