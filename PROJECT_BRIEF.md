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
- API and CLI workflows are enough for MVP so a test project can start using the system before the web UI exists.
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
- Task ownership/assignment for either an agent name or a human operator.
- Status and task event history; the first implementation may use append-only logging before richer query/reporting behavior.
- Agent-focused Markdown memory and handoff files until the database-backed context workflow is mature.
- Curl smoke checks and containerized Python integration tests.

## Nice To Include

- Web UI for humans to inspect projects, tasks, agents, runs, and events after API/CLI MVP is usable.
- Optional Prometheus metrics endpoint that can be enabled for local homelab monitoring.
- Future authentication/authorization backed by an IDP once private-network MVP behavior is proven.
- Future HashiCorp Vault integration for deployment secrets.
- Git integration for repository metadata and branch/commit status.
- OpenCode automation integration for scheduled runs.
- Review dashboard for cloud-agent findings and refactor tasks.
- Export or mirror commands that generate `TODO.md`, `MEMORY.md`, or status summaries from database state.

## Out Of Scope

- Multi-tenant public SaaS behavior in the initial release.
- Authentication/authorization for the private-network MVP; local LAN use can start without auth while an IDP is researched for later.
- Replacing Git as the source of truth for source code.
- Storing raw long-form chat transcripts in the application database by default.
- Directly reading Ansible secrets into the repo or committing any database credentials.

## Technical Preferences

- Preferred language/runtime: Python 3.14 latest for the API and worker scripts.
- Preferred framework: Flask for APIs.
- Preferred package manager: `uv` for Python.
- Preferred CLI stack: Go 1.26 with Cobra and Viper.
- Preferred database/storage: PostgreSQL.
- Local development: Docker and Docker Compose with a local PostgreSQL container.
- Preferred post-MVP web stack: React with Node.js 24 LTS, latest npm, and Express.
- Deployment target: Docker Compose VM first; K3s on the Proxmox cluster is a future feature.
- Database hosts: local Docker container for local dev, `postgresql-dev` for dev, `postgresql-stage` for stage, and `postgresql`/`postgresql.taylor.lan` for prod via environment-injected `DATABASE_URL` or equivalent secret mechanism.
- Environment flag: `APP_ENV=local|dev|stage|prod`; deployed runtime should default to `prod`, while local commands must set `APP_ENV=local` explicitly.
- Secrets: production/dev/stage credentials live outside Git; Ansible secrets are referenced only as an operational source, not read or copied by agents. Docker Compose deployments should use env files or Compose secrets first; HashiCorp Vault is a future integration candidate.
- Authentication requirements: private-network MVP can start without auth; research an IDP-backed model before exposing beyond the trusted LAN or broadening use.
- Observability: Prometheus integration should be optional and easy to enable; Jason's Prometheus server is `prometheus.taylor.lan`.
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

- Confirm exact Python 3.14 patch version during scaffolding.
- Confirmed: MVP is API plus CLI/scripts; web UI follows for human review and ad hoc task entry.
- Confirmed: initial use is private LAN/local homelab; authentication is deferred and IDP research is future work.
- Confirmed: all environments use database `agent_workbench`, schema `agent_workbench`, user `agent_workbench`, on separate hosts (`postgresql-dev`, `postgresql-stage`, `postgresql`). Secret injection: Docker Compose env files first; Vault as future research.
- Confirm exact OpenCode scheduled-run command once stub CLI commands exist.
