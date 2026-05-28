# Agent Workflow

Operating loop for local and cloud agents working on `Agent Workbench`.

## Single Agent Mode

Use this mode if you are running an agent manually rather than on a schedule.

1. Read `AGENTS.md`.
2. Read `PROJECT_BRIEF.md`, `MEMORY.md`, and relevant docs in `docs/`.
3. Check `git status`.
4. Pick the highest-priority unblocked task via `awb task next`, or follow the
   user's explicit task. (`TODO.md` is a read-only historical reference.)
5. Claim the task: `awb task claim <task-id>`.
6. Run the Contract Preflight if the task touches API, database, CLI/scripts,
   Docker, deployment, or workflow docs.
7. Implement only that task.
8. Run the most relevant validation available.
9. Update `MEMORY.md` and docs when behavior or contracts change.
10. Mark the task complete or blocked via `awb task complete / block`.
11. Summarize changes, validation, blockers, and follow-up.

## Contract Preflight

Run this quick check before implementation tasks.

1. Identify the contract touched by the task: route, request/response JSON, CLI/script command, config, environment variable, database schema, state transition, build artifact, or agent workflow.
2. Search the repo for current and previous names of that contract.
3. Check all affected surfaces: API code, docs, scripts/CLI, tests, Docker/Compose, README/development docs, and TODO.
4. If surfaces disagree, prefer a small alignment task before adding new features.
5. Record unresolved drift in `TODO.md` rather than silently carrying it forward.

## Local Agent Loop (Dogfood Mode)

The workbench API is live at `https://awb-api.taylor.lan`. Use the `awb` CLI for all task and status coordination — `status.yaml` is deprecated and `TODO.md` is a read-only historical reference.

For unattended scheduled runs use `scripts/opencode-run.sh` (see
`docs/OpenCode-Workflow.md`). For manual or CI-driven runs follow this loop:

1. Pull the latest changes.
2. Read `AGENTS.md`, `PROJECT_BRIEF.md`, `MEMORY.md`, and any docs relevant
   to the candidate task.
3. Find and claim the next task:
   ```
   awb task next --output json        # inspect
   awb task claim <task-id>           # claim (sets status → in_progress)
   ```
4. Work only that task.
5. Send periodic heartbeats during long work:
   ```
   awb task heartbeat <task-id>
   ```
6. Run the most relevant validation.
7. Update docs when behavior, API contracts, or setup changes.
8. On completion:
   ```
   awb task complete <task-id> --evidence "<summary>"
   ```
9. If blocked:
   ```
   awb task block <task-id> --reason "<reason>"
   ```
10. Commit completed work. Do not push unless the project workflow
    explicitly calls for it.

Set `AWB_API_URL`, `AWB_PROJECT`, and `AWB_AGENT` via environment or `--flag`.
The CLI binary is at `cli/builds/awb`. See `AGENTS.md` for the full command
reference.

## Done Criteria

A task is done only when implementation and project state agree.

- The change is implemented or explicitly documentation-only.
- Public contracts are aligned across API, scripts/CLI, docs, tests, database, and deployment config where relevant.
- The most relevant validation command has passed, or the validation gap is documented in `TODO.md` and `MEMORY.md`.
- Stale TODO wording, old endpoint paths, and duplicate completed items are cleaned up.
- Project status is updated via `awb status create` or `awb status update` to reflect the new state.

Do not move a task to Done based only on generated code, a partial build, or an assumption that another module will be updated later.

## Task Selection Rules

Prefer tasks in this order:

1. Highest-impact unblockers for API/CLI MVP architecture, data model, and scaffolding.
2. Contract drift between docs, implementation, tests, and agent-facing commands.
3. Broken builds, failing tests, or safety/security issues.
4. Requirements and architecture tasks that unblock many later tasks.
5. Project scaffolding and developer experience.
6. Core feature implementation.
7. Tests and validation gaps.
8. Documentation and deployment tasks.
9. Cleanup tasks.

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
2. Run `awb task block <task-id> --reason "<exact blocker>"`.
3. Update project status: `awb status create --status blocked --phase <phase> --reason "<blocker summary>"`.
4. Update `MEMORY.md` with the blocker and what is needed to unblock.
5. Notify through the configured workflow manager if available.

Do not guess current external APIs, pricing, laws, platform rules, account flows, production behavior, or security-sensitive behavior.

## Bootstrap Script Rules

Run each `./scripts/` command as its own standalone Bash call — one script per invocation. Do not chain bootstrap commands with `&&`, `;`, or pipes in a single call. The Claude Code permission rule `Bash(./scripts/*)` matches the full command string; a compound like `./scripts/task-claim <id> && echo done` will not match and will prompt for approval.

- Correct: separate calls — `./scripts/task-claim <id>` then `./scripts/task-complete <id>`.
- Wrong: `./scripts/task-claim <id> && ./scripts/task-complete <id>`.

See `docs/Bootstrap-CLI.md` for the full command reference.

## Chat Logs And Agent Output

Session logs are local-only — write to `.agents/chat/` (gitignored). Formal review documents go in `docs/reviews/` and are committed.

For each meaningful session, add a concise Markdown log under `.agents/chat/` so chat reasoning can be cross-referenced if `MEMORY.md` gets out of sync.

- Use `.agents/chat/YYYY-MM-DD-HHMM-<agent>-<topic>.md`.
- Capture objective, task id(s), key decisions, commands/validation, blockers, and next steps.
- Never include secrets, credentials, tokens, or private keys.
- Cloud or human review outputs: commit to `docs/reviews/` so they are accessible on fresh clones.

Workflow managers should copy transcripts and task outputs to external storage. Hermes-compatible defaults:

- Runtime logs: `/var/log/hermes`
- Mirrored logs: `/mnt/hermes/logs`
- Project outputs and transcripts: `/mnt/hermes/output/<project-name>/`

For OpenCode, n8n, OpenClaw, or another manager, use equivalent configured output storage.
