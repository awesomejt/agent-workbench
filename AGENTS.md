# Instructions for AI Coding Assistants

Start here before doing any work in `agent-workbench`.

This project is the future source-of-truth service for coordinating AI agents across many Git-controlled projects. The repo is intentionally documentation-heavy at first because local agent context resets are lossy; concise Markdown memory remains useful until the database/API workflow can fully replace it.

## Project Boundary

Work in `agent-workbench` unless Jason explicitly names another repository as the target. Other local projects, especially `/shared/projects/dev/project-status`, are source material and learning references only.

If the IDE context, shell working directory, chat history, or open tabs point at mixed projects, pause and confirm the intended target before editing files. Do not apply `project-status` implementation details directly to this repo without checking `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, and the current Agent Workbench contracts.

## Agent Priorities

1. Preserve the product direction: modular monolith, PostgreSQL 18 source of truth, multiple project types, and agent-safe task coordination.
2. Build the smallest correct change that advances the highest-priority unblocked task.
3. Keep public contracts aligned across API docs, implementation, CLI/scripts, tests, deployment config, and Markdown handoff docs.
4. Prefer readable, maintainable code with focused tests and integration checks over broad rewrites.
5. Keep `TODO.md`, `MEMORY.md`, docs, and `status.yaml` current until the app can generate or mirror that state from Postgres.
6. Stop and mark blockers clearly when a human decision, credential, external service, or unsafe operation is required.

## Required First Reads

Before starting a task, read:

- `PROJECT_BRIEF.md`
- `MEMORY.md`
- `TODO.md`
- `status.yaml`
- `docs/Requirements.md`
- `docs/Tech-Stack.md`
- Any source, test, or config files directly relevant to the task

If the task affects architecture, API shape, data model, deployment, or local/agent workflow, also read:

- `docs/Architecture.md`
- `docs/Implementation.md`
- `AGENT_WORKFLOW.md`
- `QUALITY_CHECKLIST.md`

## Root Contract

- `AGENTS.md` - agent operating instructions.
- `README.md` - human-facing overview and setup.
- `TODO.md` - task lanes, priorities, blockers, and completed work.
- `MEMORY.md` - persistent project memory, decisions, milestones, and run notes.
- `status.yaml` - shared workflow state for humans and automation.
- `PROJECT_BRIEF.md` - product goals, constraints, users, and source material.
- `AGENT_WORKFLOW.md` - recurring local-agent, cloud-agent, and review workflow.
- `QUALITY_CHECKLIST.md` - pre-review, pre-PR, and pre-release quality gate.
- `docs/` - requirements, architecture, implementation plan, technical stack, and development notes.

## Source Of Truth Rules

- Git is the source of truth for source code, migrations, docs, and deployment definitions.
- PostgreSQL 18. Do not use SQLite. It is the intended source of truth for project/task/status/agent/run state once bootstrapped.
- Markdown files are a context bridge for humans and local agents, not the long-term coordination database.
- Until the API/CLI exists, keep Markdown files accurate and concise; later, prefer generating or mirroring summaries from Postgres.
- Do not commit secrets, database credentials, private keys, local env files, or raw transcripts.
- Ansible secrets may be referenced operationally but must never be copied into this repo.

## Engineering Rules

- Check `git status` before editing.
- Pull latest changes before starting when network and permissions allow.
- Do not overwrite user changes.
- Keep edits focused and reviewable.
- Follow the project's selected stack, formatting, naming, and architecture.
- Add or update tests for meaningful behavior changes.
- Run the most relevant validation before finishing.
- Update docs when behavior, setup, deployment, database schema, API contracts, or public interfaces change.
- Prefer migrations over ad hoc schema creation once the database is introduced.
- Keep local/dev/stage/production configuration environment-driven.
- Treat `APP_ENV` and `DATABASE_URL` as a safety boundary; never guess or synthesize dev/stage/prod credentials.

## Contract And Validation Discipline

Prevent drift between docs, API, CLI, scripts, tests, and deployment config.

- Treat public contracts as shared source material: API routes, request/response JSON, CLI commands, script names, config names, environment variables, database schema, state transitions, idempotency behavior, and build outputs.
- Review `TODO.md` during each session and add or update tasks when new work is discovered, especially during research/planning, scaffolding, and early implementation.
- Before changing API behavior, read the relevant docs, tests, clients/scripts, and TODO items.
- When changing a public contract, update all affected surfaces in the same task or leave explicit TODOs if the task is intentionally planning-only.
- Do not mark a task complete just because code was written. Done requires the relevant validation to pass, or a clearly documented blocker/test gap.
- Prefer small vertical changes that keep API, scripts/CLI, tests, docs, and deployment config aligned.
- Search for old names and paths after migrations.
- Verify tests exercise the actual app shape, not an older or imagined interface.

## Agent Coordination Design Rules

When designing or implementing coordination features:

- Use atomic task claims with leases or expiration.
- Use heartbeats for long-running agent work.
- Use optimistic locking or version checks for state changes.
- Use idempotency keys for agent-submitted actions that may retry.
- Record append-only events for task/project/status transitions.
- Make invalid state transitions impossible or explicit.
- Keep review findings and validation evidence durable.
- Favor database-backed coordination over repo-file edits as soon as the bootstrap tooling exists.

## Status Workflow

Use `status.yaml` as the shared state file until the app can manage this state:

- `active` - work may proceed.
- `paused` - do not perform automated work.
- `blocked` - waiting on a human decision, credential, source file, or validation.
- `working` - a human or agent is actively changing the repo; other agents should skip.
- `error` - repo or automation state is unsafe; stop and request recovery.
- `stopped` - project is complete or intentionally shut down.

Automated agents should set `working` only while actively editing, and return to `active`, `blocked`, `error`, or `stopped` before ending a run.

## Task Selection

Prefer tasks in this order unless `TODO.md` says otherwise:

1. Blocker removal and requirements clarification.
2. Contract drift across docs, API, scripts/CLI, tests, database, and deployment config.
3. Failing tests, broken builds, safety issues, or security-sensitive problems.
4. Architecture/data model/scaffolding that unlocks later work.
5. Core implementation tasks.
6. Tests, smoke checks, and integration validation.
7. Documentation, deployment notes, and cleanup.

## Cloud Review Gate

Before real use, release, or deployment, schedule a cloud-based AI review/refactor pass from `TODO.md`.

- Cloud review should prioritize correctness, contract alignment, test reliability, maintainability, data integrity, security-sensitive assumptions, and production-readiness risks.
- Review findings should be added to `TODO.md` before broad refactors begin.
- Refactors should be split by module or contract boundary and validated with the root workflow once it exists.
- Do not treat local-loop generated code as production-ready until the cloud review/refactor lane and relevant validation have completed.

## Chat Logs And External Agent Logs

Full chat transcripts should not be committed. Use `chats/` only as a local transcript workspace; Markdown transcript files there are ignored by Git.

Agents should write a concise Markdown run note in `chats/` for each meaningful work session so Jason can cross-reference decisions when `MEMORY.md` and task state drift.

- File naming: `chats/YYYY-MM-DD-HHMM-<agent>-<topic>.md`.
- Include: objective, task id(s), files changed, key reasoning/decision points, validation run, blockers, and follow-up.
- Keep notes concise and redact secrets, credentials, and private keys.
- Treat `MEMORY.md` as durable summary and `chats/` as higher-detail local context.

Agent workflow managers should copy or mirror transcripts and runtime logs to external storage. Hermes-compatible defaults are:

- Runtime logs: `/var/log/hermes`
- Mirrored logs: `/mnt/hermes/logs`
- Project output and transcripts: `/mnt/hermes/output/<project-name>/`

For OpenCode, n8n, OpenClaw, or another orchestrator, use equivalent configured storage.

## Stop Conditions

Stop and mark a task blocked if:

- Required source files or requirements are missing.
- A decision depends on Jason's preference.
- Credentials, paid services, account access, or production systems are required.
- The next action could be destructive or security-sensitive.
- External facts, product APIs, laws, pricing, or platform rules must be current and cannot be verified.
