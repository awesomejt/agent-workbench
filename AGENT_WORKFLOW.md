# Agent Workflow

Operating loop for local and cloud agents working on `Agent Workbench`.

## Single Agent Mode

Use this mode if you are running an agent manually rather than on a schedule.

1. Read `AGENTS.md`.
2. Read `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, and `status.yaml`.
3. Read relevant docs in `docs/`.
4. Check `git status`.
5. Pick the highest-priority unblocked task from `TODO.md`, or follow the user's explicit task.
6. Run the Contract Preflight if the task touches API, database, CLI/scripts, Docker, deployment, or workflow docs.
7. Implement only that task.
8. Run the most relevant validation available.
9. Update `TODO.md`, `MEMORY.md`, and docs.
10. Summarize changes, validation, blockers, and follow-up.

## Contract Preflight

Run this quick check before implementation tasks.

1. Identify the contract touched by the task: route, request/response JSON, CLI/script command, config, environment variable, database schema, state transition, build artifact, or agent workflow.
2. Search the repo for current and previous names of that contract.
3. Check all affected surfaces: API code, docs, scripts/CLI, tests, Docker/Compose, README/development docs, and TODO.
4. If surfaces disagree, prefer a small alignment task before adding new features.
5. Record unresolved drift in `TODO.md` rather than silently carrying it forward.

## Local Agent Loop

Use this loop for OpenCode, a persistent local agent, scheduled runner, or workflow manager.

1. Pull the latest changes.
2. Read `AGENTS.md`, `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, and `status.yaml`.
3. Append a wake entry to external log storage.
4. Act on `status.yaml`:
   - `stopped` - halt.
   - `paused` - halt without work.
   - `blocked` - halt until the blocker is resolved.
   - `working` - another worker is active; skip this cycle.
   - `error` - halt and require human recovery.
   - `active` - continue.
5. Check for unresolved placeholders in required root files.
6. Pick the highest-priority unblocked task from `AI Agent Work`.
7. Move that task to `In Progress` if multiple agents may run.
8. Set `status.yaml` to `working`.
9. Work only that task.
10. Run appropriate tests, checks, or builds.
11. Update `TODO.md`, `MEMORY.md`, and relevant docs.
12. If blocked, move the task to `Blocked`, add a `Needs Attention` item, set `status.yaml` to `blocked`, and stop.
13. If complete and validated, move the task to `Done` and return `status.yaml` to `active`.
14. Commit and push only when the project workflow explicitly calls for it.

## Done Criteria

A task is done only when implementation and project state agree.

- The change is implemented or explicitly documentation-only.
- Public contracts are aligned across API, scripts/CLI, docs, tests, database, and deployment config where relevant.
- The most relevant validation command has passed, or the validation gap is documented in `TODO.md` and `MEMORY.md`.
- Stale TODO wording, old endpoint paths, and duplicate completed items are cleaned up.
- `status.yaml` is returned to `active`, `blocked`, `error`, or `stopped`.

Do not move a task to Done based only on generated code, a partial build, or an assumption that another module will be updated later.

## Task Selection Rules

Prefer tasks in this order:

1. Contract drift between docs, implementation, tests, and agent-facing commands.
2. Broken builds, failing tests, or safety/security issues.
3. Requirements and architecture tasks that unblock many later tasks.
4. Project scaffolding and developer experience.
5. Core feature implementation.
6. Tests and validation gaps.
7. Documentation and deployment tasks.
8. Cleanup tasks.

Do not perform manual validation tasks unless Jason explicitly asks. Prepare checklists or scripts for them instead.

## Review Mode

Use this mode before real use, release, deployment, or large refactors. It is especially appropriate for a cloud-based AI agent with larger context.

1. Read all root contract files, docs, source, tests, and configs.
2. Build a contract map for API routes, request/response JSON, CLI/scripts, database schema, Docker services, environment variables, and build artifacts.
3. Compare the contract map against implementation and tests.
4. Run available validation, or document why validation cannot run.
5. Add findings to the `Review` section in `TODO.md`, ordered by risk.
6. Refactor only after findings are captured and the work can be split into focused, validated changes.

Cloud review should emphasize correctness, integration behavior, maintainability, test reliability, data integrity, and production-readiness.

## Blocker Handling

If blocked:

1. Stop the task.
2. Move it to `Blocked` in `TODO.md`.
3. Add the exact decision, credential, source file, account access, or validation needed.
4. Add a short entry to `Needs Attention`.
5. Update `status.yaml` with `status: blocked`, the reason, phase, worker, and timestamp.
6. Update `MEMORY.md`.
7. Notify through the configured workflow manager if available.

Do not guess current external APIs, pricing, laws, platform rules, account flows, production behavior, or security-sensitive behavior.

## Chat Logs And Agent Output

Full transcripts are not committed. Temporary local transcripts may be kept under `chats/`, but Markdown files there are ignored by Git.

Workflow managers should copy transcripts and task outputs to external storage. Hermes-compatible defaults:

- Runtime logs: `/var/log/hermes`
- Mirrored logs: `/mnt/hermes/logs`
- Project outputs and transcripts: `/mnt/hermes/output/<project-name>/`

For OpenCode, n8n, OpenClaw, or another manager, use equivalent configured output storage.
