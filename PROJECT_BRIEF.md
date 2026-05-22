# Project Brief

## Project Identity

- Project name: `Agent Workbench`
- Short name: `agent-workbench`
- Repository: `agent-workbench`
- Project type: `full-stack agent coordination platform`
- Primary users: AI coding agents and Jason

## Purpose

`Agent Workbench` is an API-driven project management and coordination system for AI agents working across many Git-controlled projects. It moves volatile agent coordination state out of per-repo Markdown files and into a Postgres-backed source of truth while keeping concise Markdown handoff files available for context reset, audits, and human readability.

The system should help agents discover projects, claim tasks, report status, append durable run notes, avoid duplicate work, and leave reviewable evidence of decisions and validation.

## Success Criteria

The project is successful when:

- A modular API can track multiple projects, tasks, status records, agents, runs, and append-only events in PostgreSQL.
- Agents can safely claim, heartbeat, block, complete, and review tasks using atomic state transitions.
- Local development uses a PostgreSQL container, while dev, stage, and production can use configured PostgreSQL hosts such as `postgresql.taylor.lan` without committing secrets.
- A CLI and lightweight scripts can bootstrap agent workflows before the full web UI exists.
- Project metadata can describe different project types, source locations, default agents, and workflow defaults.
- Markdown files remain available as compact context handoff artifacts, but the database/API is the preferred source of truth once available.
- Cloud review/refactor is planned before real use or production deployment.

## Users And Workflows

- Primary user: AI coding agents running in local loops, cloud review sessions, or scheduled automation.
- Secondary user: Jason managing projects, agents, deployments, and review gates.
- Most important workflow: agent discovers and claims the highest-priority unblocked task for a project.
- Repeated or high-frequency workflow: agent updates task status, appends run events, and heartbeats while working.
- Admin or maintenance workflow: Jason creates projects, selects default agents, configures environments, and reviews production readiness.

## Must Include

- Multi-project tracking for Git-controlled projects.
- Project modules/sections with project-wide/general fallback for status and tasks.
- Modular API namespaces for project info, project status, tasks, agents, runs, and events.
- PostgreSQL-backed source of truth with migrations.
- Local PostgreSQL container for development.
- Environment-driven database URLs for local, dev, stage, and production.
- Target database/schema policy for local, dev, stage, and prod, with `APP_ENV`/`--env` selection.
- Safe task claiming with leases, heartbeats, idempotency keys, and append-only event history.
- Project type metadata for software development, websites, books, courses, web articles, automation, and future project categories.
- Phase tracking for status and tasks across planning, research, implementation, testing, and review.
- Default agent selection and workflow hints per project type.
- Bootstrap scripts or CLI commands that can operate before the full web UI exists.
- Agent-focused Markdown memory and handoff files until the database-backed context workflow is mature.
- Curl smoke checks and containerized Python integration tests.

## Nice To Include

- Web UI for humans to inspect projects, tasks, agents, runs, and events.
- Git integration for repository metadata and branch/commit status.
- OpenCode automation integration for scheduled runs.
- Review dashboard for cloud-agent findings and refactor tasks.
- Export or mirror commands that generate `TODO.md`, `MEMORY.md`, or status summaries from database state.

## Out Of Scope

- Multi-tenant public SaaS behavior in the initial release.
- Production authentication/authorization beyond what is needed for Jason's private network deployment.
- Replacing Git as the source of truth for source code.
- Storing raw long-form chat transcripts in the application database by default.
- Directly reading Ansible secrets into the repo or committing any database credentials.

## Technical Preferences

- Preferred language/runtime: Python for the API and worker scripts unless implementation planning chooses otherwise.
- Preferred framework: FastAPI or Flask; choose during stack finalization based on API documentation, typing, and implementation ergonomics.
- Preferred package manager: `uv` for Python.
- Preferred database/storage: PostgreSQL.
- Local development: Docker and Docker Compose with a local PostgreSQL container.
- Deployment target: Docker Compose VM first, with K3s on the Proxmox cluster as a later option.
- Production database: `postgresql.taylor.lan` via environment-injected `DATABASE_URL` or equivalent secret mechanism.
- Environment flag: `APP_ENV=local|dev|stage|prod`; deployed runtime should default to `prod`, while local commands must set `APP_ENV=local` explicitly.
- Secrets: production/dev/stage credentials live outside Git; Ansible secrets are referenced only as an operational source, not read or copied by agents.
- Authentication requirements: private-network MVP can start minimal, but production access model must be decided before real use.
- Accessibility or browser/device support: web UI should support current evergreen desktop browsers and keyboard-accessible workflows.

## Source Material

| Source | Path or URL | How to use it |
| --- | --- | --- |
| Project Status prototype | `/shared/projects/dev/project-status` | Mine for lessons, agent workflow docs, smoke/integration test ideas, and status module concepts. Do not blindly copy implementation bugs. |
| OpenCode setup repo | `/shared/projects/ai/opencode-setup` | Store OpenCode prompts, agent definitions, configuration notes, and scheduled-run helper scripts. |
| Local project roots | `~/projects/{ai,courses,dev,infra}` | Default discovery roots for existing Git-controlled projects; keep configurable. |
| Ansible project | `~/projects/infra/ansible` | Reference deployment and secret conventions. Do not copy secrets into this repo. |
| Production PostgreSQL | `postgresql.taylor.lan` | Target production database host after deployment/secret handling is confirmed. |
| Template workflow docs | Root docs in this repo | Keep AGENTS, TODO, MEMORY, and workflow docs aligned until the API can become the source of truth. |

## Validation Needed

- Confirm final API framework: FastAPI, Flask, or another Python framework.
- Confirm whether the first web UI should be included in MVP or follow the CLI/API bootstrap.
- Confirm production authentication and network exposure expectations.
- Confirm dev/stage/production database names, users, schema layout, and secret injection approach.
- Confirm whether OpenCode scheduled runs should interact through CLI, API, or both during bootstrap.
