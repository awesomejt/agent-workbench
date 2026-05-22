# Agent Workflow

Operating loop for local and cloud agents working on coding projects.

## Single Agent Mode

Use this mode if you are running an agent manually rather than on a schedule.

On each manual run:

1. Read `AGENTS.md`.
2. Read `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, and `status.yaml`.
3. Read relevant docs in `docs/`.
4. Check `git status`.
5. Pick the highest-priority unblocked task from `TODO.md`, or follow the user's explicit task.
6. Implement only that task.
7. Run the most relevant validation available.
8. Update `TODO.md`, `MEMORY.md`, and docs.
9. Summarize changes, validation, blockers, and follow-up.

## Local Agent Loop

Use this loop for a persistent local agent, scheduled runner, or workflow manager.

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
13. If complete, move the task to `Done` and return `status.yaml` to `active`.
14. Commit and push only when the project workflow explicitly calls for it.

## Task Selection Rules

Prefer tasks in this order:

1. Broken builds, failing tests, or safety/security issues.
2. Requirements and architecture tasks that unblock many later tasks.
3. Project scaffolding and developer experience.
4. Core feature implementation.
5. Tests and validation gaps.
6. Documentation and deployment tasks.
7. Cleanup tasks.

Do not perform manual validation tasks unless Jason explicitly asks. Prepare checklists or scripts for them instead.

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

For n8n, OpenClaw, or another manager, use equivalent configured output storage.
