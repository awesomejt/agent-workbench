# Project Agent Starter Kit

Agentic starter template for AI-assisted coding projects: frontend apps, backend services, CLIs, automation tools, libraries, websites, and mixed-stack software projects.

This template is designed for agents that can pick a task, update status, make focused code changes, run validation, document results, and commit coherent work when asked.

## Root Contract

AI assistants and humans should start with the root files:

- `AGENTS.md` - coding-project agent operating instructions.
- `README.md` - human-facing overview and setup.
- `TODO.md` - task lanes for discovery, planning, implementation, validation, blockers, and done items.
- `MEMORY.md` - persistent project decisions, milestones, blockers, and run notes.
- `status.yaml` - current agent workflow state.
- `PROJECT_BRIEF.md` - project goals, audience/users, constraints, stack preferences, and source material.
- `AGENT_WORKFLOW.md` - recurring local-agent workflow.
- `QUALITY_CHECKLIST.md` - engineering quality checklist before review or release.

## Intended Workflow

1. Fill out `PROJECT_BRIEF.md`.
2. Fill in `docs/Requirements.md` and `docs/Tech-Stack.md`.
3. A local or cloud agent reads `AGENTS.md`, `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, and `status.yaml`.
4. The agent works the highest-priority unblocked engineering task.
5. The agent updates code, tests, docs, `TODO.md`, and `MEMORY.md`.
6. If the workflow calls for it, the agent commits a small logical change.
7. Jason reviews product decisions, security-sensitive behavior, deployments, and release readiness.

## Supporting Folders

- `docs/` - requirements, architecture, tech stack, implementation plan, and diagrams.
- `src/` - project source when the generated project has source code.
- `tests/` - project tests when applicable.
- `chats/` - optional local transcript workspace. Transcript files are ignored by Git.
- `working/` - temporary scratch files ignored by Git.
- `build/` - build artifacts ignored by Git.

## Chat Logs And Agent Output

Full chat transcripts are useful context but should not be committed by default. Keep temporary local transcripts under `chats/` if helpful. Workflow managers should copy or mirror transcripts and runtime logs to external storage.

Hermes-compatible defaults:

- Runtime logs: `/var/log/hermes`
- Mirrored logs: `/mnt/hermes/logs`
- Project output and transcripts: `/mnt/hermes/output/<project-name>/`

For n8n, OpenClaw, or another orchestrator, use equivalent configured storage.

## Git Setup

After creating a new project from this template:

```bash
git config commit.template .gitmessage
```

Use Conventional Commits and keep AI attribution in commit messages.
