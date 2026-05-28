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
5. Keep `MEMORY.md` and docs current; record new work as tasks in the workbench API rather than updating `TODO.md` or `status.yaml`.
6. Stop and mark blockers clearly when a human decision, credential, external service, or unsafe operation is required.

## Task Workflow (Dogfood Mode)

The workbench API is live. Use the `awb` CLI for all task operations — it is the authoritative source for what to work on.

```
# Find available tasks
AWB_API_URL=http://localhost:8000 AWB_PROJECT=<slug> AWB_AGENT=<name> awb task list --available

# Claim a task
awb task claim <task-id>

# Heartbeat (renew lease during long work)
awb task heartbeat <task-id>

# Complete
awb task complete <task-id> --evidence "summary of work done"

# Mark blocked
awb task block <task-id> --reason "reason"

# Create a new task when you discover work (use instead of editing Markdown)
awb task create --title "Do the thing" --phase implementation --priority 50
```

**Per-repo config** — if `.awb/config.yaml` exists in the working directory it is loaded automatically (no flags required for `project` and `api_url`). Create one with:

```bash
awb init --project <slug>   # writes .awb/config.yaml
```

Otherwise set `AWB_API_URL`, `AWB_PROJECT`, and `AWB_AGENT` via environment or `--flag` on each call. The CLI binary is at `cli/builds/awb` in the repo root; install with `make install-cli`.

Task selection order: highest `priority` first, then oldest `created_at`. Prefer tasks with `blocks` relationships unblocked before moving to lower-priority items.

## Required First Reads

Before starting a task, read:

- `PROJECT_BRIEF.md`
- `MEMORY.md`
- `docs/Requirements.md`
- `docs/Tech-Stack.md`
- Any source, test, or config files directly relevant to the task

`TODO.md` is a read-only historical reference. Do not update it; use the workbench API.

If the task affects architecture, API shape, data model, deployment, or local/agent workflow, also read:

- `docs/Architecture.md`
- `docs/Implementation.md`
- `AGENT_WORKFLOW.md`
- `QUALITY_CHECKLIST.md`

## Root Contract

- `AGENTS.md` - agent operating instructions (this file).
- `README.md` - human-facing overview and setup.
- `TODO.md` - historical task reference; read-only. Active tasks live in the workbench API.
- `MEMORY.md` - persistent project memory, decisions, and milestones.
- `status.yaml` - **deprecated**. Project status is now tracked via `awb status show/create/update`. This file is kept as a last-resort fallback if the API is unreachable.
- `PROJECT_BRIEF.md` - product goals, constraints, users, and source material.
- `AGENT_WORKFLOW.md` - recurring local-agent, cloud-agent, and review workflow.
- `QUALITY_CHECKLIST.md` - pre-review, pre-PR, and pre-release quality gate.
- `docs/` - requirements, architecture, implementation plan, technical stack, and development notes.

## Source Of Truth Rules

- Git is the source of truth for source code, migrations, docs, and deployment definitions.
- PostgreSQL 18. Do not use SQLite. It is the intended source of truth for project/task/status/agent/run state once bootstrapped.
- Markdown files are a context bridge for humans and local agents, not the long-term coordination database.
- The workbench API and `awb` CLI are operational — task and project state lives in Postgres. Do not mirror task state back into Markdown.
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
- When new work is discovered during a session, create it as a task via `awb task create --title "..." --phase <phase> --priority <n>` rather than editing Markdown files.
- Before changing API behavior, read the relevant docs, tests, clients/scripts, and TODO items.
- When changing a public contract, update all affected surfaces in the same task or leave explicit TODOs if the task is intentionally planning-only.
- Do not mark a task complete just because code was written. Done requires the relevant validation to pass, or a clearly documented blocker/test gap.
- Prefer small vertical changes that keep API, scripts/CLI, tests, docs, and deployment config aligned.
- Search for old names and paths after migrations.
- Verify tests exercise the actual app shape, not an older or imagined interface.

## Phase Vocabulary

The canonical project phases, in order:

| Ordinal | Phase | Typical task types |
|---|---|---|
| 1 | `discovery` | research, exploration, requirements gathering, spikes |
| 2 | `design` | architecture, planning, outlines, curriculum design |
| 3 | `implementation` | code, content creation, configuration, writing |
| 4 | `testing` | QA, validation, fact-checking, integration tests |
| 5 | `review` | code review, editorial review, signoff, release prep |

When creating a task, set `phase` to the phase where the work categorically belongs — not the current project phase. A research spike added mid-implementation still has `phase = discovery`.

Project phase (tracked in `project_statuses`) is a forward-only high-water mark. It advances automatically when the first task of a later phase is claimed; it never moves backward.

## Agent Roles and Model Tiers

Tasks carry a `role` and a `model_tier` set during triage.

**Roles** (abstract; interpretation depends on project type):

| Role | Code project | Course/book/content project |
|---|---|---|
| `researcher` | tech research, spikes | topic research, source gathering |
| `planner` | architecture, design decisions | outline, curriculum design |
| `implementer` | programmer | content creator |
| `writer` | docs, READMEs, guides | prose, narrative |
| `reviewer` | code reviewer | editorial reviewer |
| `tester` | QA, integration validation | accuracy/fact checker |
| `orchestrator` | triage, decomposition, routing | same |

**Model tiers:**

- `cloud` — tasks requiring judgment, nuance, or broad knowledge: discovery-phase work, design review, any review-phase task, complex orchestration decisions.
- `local` — tasks suited to structured, well-defined execution: design first pass, implementation first pass, testing, documentation.

These are defaults. The orchestrator may override `model_tier` per task when the default does not fit.

## Triage Protocol (Orchestrator Agents)

The orchestrator claims tasks with `status = new` from the project's triage queue.

For each `new` task, the orchestrator must:

1. Evaluate whether the request is valid and non-duplicate.
   - If duplicate: set `status = duplicate`, create a `duplicates` relationship to the original task.
   - If invalid/out of scope: set `status = rejected` with a reason in the summary.
2. Optionally decompose into sub-tasks (same project only). Sub-tasks should have `relationship_type = subtask_of` pointing to the parent.
3. Set `role` and `model_tier` on each resulting task.
4. Set `phase` to the appropriate ordinal position.
5. Set `status = pending` on tasks ready for worker agents to claim.

Do not create tasks in other projects. Inbox is always per-project.

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

Project status is tracked via the workbench API. Use `awb status` commands — do not edit `status.yaml`.

```bash
# View current status
awb status show

# Create a new status record (e.g. on session start)
awb status create --status active --phase <phase> --summary "starting work on X"

# Update an existing record (requires --version from the current record)
awb status update <id> --status blocked --reason "waiting on Y" --version <n>
```

Valid status values:

- `active` - work may proceed.
- `paused` - do not perform automated work.
- `blocked` - waiting on a human decision, credential, source file, or validation.
- `working` - a human or agent is actively changing the repo; other agents should skip.
- `error` - repo or automation state is unsafe; stop and request recovery.
- `stopped` - project is complete or intentionally shut down.

Automated agents should set `working` before editing and return to `active`, `blocked`, `error`, or `stopped` before ending a run. If `awb-api.taylor.lan` is unreachable, fall back to `status.yaml` as a last resort.

## Task Selection

Use `awb task list --available` to find claimable tasks. Prefer tasks in this order:

1. Blocker removal and requirements clarification.
2. Contract drift across docs, API, scripts/CLI, tests, database, and deployment config.
3. Failing tests, broken builds, safety issues, or security-sensitive problems.
4. Architecture/data model/scaffolding that unlocks later work.
5. Core implementation tasks.
6. Tests, smoke checks, and integration validation.
7. Documentation, deployment notes, and cleanup.

## Cloud Review Gate

Before real use, release, or deployment, schedule a cloud-based AI review/refactor pass. Create a review task in the workbench API with `role=reviewer`, `model_tier=cloud`.

- Cloud review should prioritize correctness, contract alignment, test reliability, maintainability, data integrity, security-sensitive assumptions, and production-readiness risks.
- Review findings should be filed as new tasks (or added to the review task's evidence) before broad refactors begin.
- Refactors should be split by module or contract boundary and validated with the full test suite.
- Do not treat local-loop generated code as production-ready until the cloud review/refactor lane and relevant validation have completed.

## Chat Logs And External Agent Logs

Session logs are local-only — write them to `.agents/chat/` which is gitignored. Formal review documents (cloud or human review artifacts) belong in `docs/reviews/` and are committed.

Agents should write a concise Markdown run note in `.agents/chat/` for each meaningful work session so Jason can cross-reference decisions when `MEMORY.md` and task state drift.

- File naming: `.agents/chat/YYYY-MM-DD-HHMM-<agent>-<topic>.md`.
- Include: objective, task id(s), files changed, key reasoning/decision points, validation run, blockers, and follow-up.
- Keep notes concise and redact secrets, credentials, and private keys.
- Treat `MEMORY.md` as durable summary and `.agents/chat/` as higher-detail local context.
- Review documents (Grok, Codex, human review): commit to `docs/reviews/` so findings stay accessible across clones.

Agent workflow managers should copy or mirror transcripts and runtime logs to external storage. Hermes-compatible defaults are:

- Runtime logs: `/var/log/hermes`
- Mirrored logs: `/mnt/hermes/logs`
- Project output and transcripts: `/mnt/hermes/output/<project-name>/`

For OpenCode, n8n, OpenClaw, or another orchestrator, use equivalent configured storage.

## Markdown File Strategy

Markdown files are a context bridge — useful for human and agent onboarding when there is no persistent memory of earlier sessions. The workbench API and PostgreSQL are authoritative for task/project/status state.

| File | Role | Who updates | When |
|---|---|---|---|
| `MEMORY.md` | Durable project narrative: decisions, milestones, architecture notes, open questions, blockers, run log | Any agent | After each meaningful session; whenever a key decision is made or reversed |
| `TODO.md` | Historical task reference; read-only after dogfood transition (2026-05-23) | No one | Never — use `awb` or the API for new tasks |
| `status.yaml` | Last-resort fallback only — deprecated | Any agent | Only when `awb-api.taylor.lan` is unreachable; use `awb status` instead |
| `.agents/chat/*.md` | High-detail per-session logs (local only, gitignored) | Agent that ran the session | After each meaningful work session |
| `docs/reviews/*.md` | Formal cloud/human review artifacts | Reviewer | When a review is complete |

**MEMORY.md update triggers:**
- A new design decision or architectural choice is made.
- A key implementation milestone is reached.
- A blocker is added or resolved.
- An open question is answered.
- The project phase advances.
- At the start of a session: update "Current Status" to reflect the actual queue state.

**What NOT to put in MEMORY.md:**
- Full chat transcripts or tool outputs (these go in `.agents/chat/`).
- Task lists (these live in the workbench API).
- Secrets, credentials, private keys, or database URLs.

**Project status snapshots:**
The `project_statuses` table in PostgreSQL is the authoritative source. MEMORY.md's "Current Status" section is a human-readable summary written by agents — it may lag slightly but should be updated each session.

## Stop Conditions

Stop and mark a task blocked if:

- Required source files or requirements are missing.
- A decision depends on Jason's preference.
- Credentials, paid services, account access, or production systems are required.
- The next action could be destructive or security-sensitive.
- External facts, product APIs, laws, pricing, or platform rules must be current and cannot be verified.
