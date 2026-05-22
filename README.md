# Agent Workbench

`Agent Workbench` is a planned API-driven project management and coordination system for AI agents working across many Git-controlled projects.

The goal is to move agent coordination state out of noisy per-repo Markdown edits and into a PostgreSQL-backed source of truth, while preserving concise Markdown handoff files for local agents whose context resets between runs.

## Direction

- One modular monolith API and one PostgreSQL database.
- Multiple internal modules instead of many small services at the start.
- Git remains the source of truth for source code.
- PostgreSQL becomes the source of truth for projects, tasks, status, agents, runs, leases, and events.
- Local development uses Docker Compose with a local PostgreSQL container.
- Dev, stage, and production use separate PostgreSQL hosts: `postgresql-dev`, `postgresql-stage`, and `postgresql`/`postgresql.taylor.lan` through environment-injected secrets.
- Environment selection uses `APP_ENV=local|dev|stage|prod`; deployed runtime should default to prod while local commands explicitly select local.

## Planned Modules

- `projects`: project metadata, Git source location, type, environment, and defaults.
- `project_status`: current status, phase, blockers, and status history.
- `project_tasks`: tasks, priorities, dependencies, leases, and completion evidence.
- `agents`: agent registry, default agents, capabilities, and runtime hints.
- `runs`: agent run attempts, heartbeats, logs, validation results, and outcomes.
- `events`: append-only audit trail for state transitions and agent activity.
- `reviews`: cloud review findings, refactor recommendations, and signoff gates.

## Bootstrap Strategy

This repo will initially use familiar agent Markdown files:

- `TODO.md`
- `MEMORY.md`
- `status.yaml`
- `AGENTS.md`
- `AGENT_WORKFLOW.md`

Once the database schema and scripts exist, the normal agent workflow should shift toward:

```bash
./scripts/task-next
./scripts/task-claim <task-id>
./scripts/task-complete <task-id>
./scripts/status-show
```

OpenCode should use these stub CLI commands first. Later, those scripts should become or wrap a real Go CLI/API workflow.

## Root Files

- `AGENTS.md` - instructions for AI coding assistants.
- `PROJECT_BRIEF.md` - product goals and constraints.
- `TODO.md` - current work queue during bootstrap.
- `MEMORY.md` - durable project memory during bootstrap.
- `status.yaml` - local agent-loop state during bootstrap.
- `docs/` - requirements, architecture, implementation, and stack notes.
- `QUALITY_CHECKLIST.md` - pre-review and release quality gate.

## Current Status

Planning/bootstrap phase. No application code should be assumed production-ready until the cloud review/refactor lane and validation gates are complete.
