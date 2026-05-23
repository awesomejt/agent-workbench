# [PROJECT_NAME] — Agent Instructions

> **Template:** Copy this file to the root of a hosted project as `AGENTS.md`.
> Replace all `[PLACEHOLDER]` values. Delete this instruction block.
> For phase, role, and model tier vocabulary see the workbench root `AGENTS.md`.

---

## Project Overview

**Project:** [PROJECT_NAME]  
**Type:** [code | course | content | research | infrastructure | other]  
**Workbench project slug:** [awb-project-slug]  
**Goal:** [One sentence: what this project builds or produces and why it matters.]

**Scope boundary:** Work in this repository only. Do not create tasks in other workbench projects or modify files outside this repo without explicit instruction.

## AWB Connection

```
AWB_API_URL=http://localhost:8000
AWB_PROJECT=[awb-project-slug]
AWB_AGENT=[your-agent-name]
```

Use `awb task list --available` to find claimable tasks. Claim before starting work; heartbeat during long sessions; complete or block when done.

## What Agents Produce Here

[Describe the primary deliverable for each role as it applies to this project type. Examples below — replace with project-specific descriptions.]

| Role | What it means on this project |
|---|---|
| `researcher` | [e.g., "technology research, spike branches, options analysis"] |
| `planner` | [e.g., "architecture decisions, task breakdowns, API contracts"] |
| `implementer` | [e.g., "working code that passes tests and matches the design spec"] |
| `writer` | [e.g., "READMEs, API guides, developer runbooks"] |
| `reviewer` | [e.g., "code review: correctness, security, maintainability findings"] |
| `tester` | [e.g., "integration test results, edge case coverage reports"] |
| `orchestrator` | Triage queue: review `new` tasks, set role/tier/phase, approve or reject |

## Model Tier Defaults

Override the workbench defaults here if this project has different cost/capability requirements.

| Phase | Default tier | Reason |
|---|---|---|
| `discovery` | `cloud` | [e.g., broad knowledge needed for research] |
| `design` | `local` | [e.g., structured planning suits local execution] |
| `implementation` | `local` | [e.g., well-defined tasks] |
| `testing` | `local` | [e.g., deterministic validation] |
| `review` | `cloud` | [e.g., judgment and nuance required] |

## Phase Expectations

[Describe what done looks like in each phase for this project. Delete phases that do not apply.]

- **discovery:** [e.g., findings document with options, tradeoffs, and a recommendation]
- **design:** [e.g., architecture doc or task breakdown an implementer can act on without clarification]
- **implementation:** [e.g., passing tests, ruff clean, migration run, session log in .agents/chat/]
- **testing:** [e.g., integration test results documented, all acceptance criteria verified]
- **review:** [e.g., structured findings with severity, location, and concrete fix suggestion]

## Local Tool Configuration

[Document any project-specific tool setup agents need. Examples:]

```bash
# Run tests
[test command]

# Lint / format
[lint command]

# Run database migrations
[migration command]

# Start dev server
[dev server command]
```

## Stop Conditions

Stop and mark a task `blocked` if:

- Required source files, credentials, or external access are missing.
- A decision depends on [OWNER_NAME]'s preference or approval.
- The next action would affect production systems, external services, or shared infrastructure.
- A design conflict is found that cannot be resolved within the task scope.

[Add any project-specific stop conditions here.]

## Handoff Conventions

- Write a session log in `.agents/chat/YYYY-MM-DD-HHMM-<agent>-<topic>.md` after each work session.
- Include: objective, task id, files changed, key decisions, validation run, and blockers.
- Committed review artifacts go in `docs/reviews/`.
- Do not commit secrets, credentials, private keys, or raw transcripts.
