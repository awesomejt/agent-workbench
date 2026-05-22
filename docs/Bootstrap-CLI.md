# Bootstrap CLI

Two interfaces are available depending on which phase the project is in (see Transition Roadmap below).

**Go CLI (`awb`)** — the primary interface once the API is running. See `docs/Tech-Stack.md` Commands section for full usage. Install with `make install-cli` or `scripts/install-awb.sh`.

**Bootstrap scripts** — Markdown-backed fallback used by OpenCode during Phase 1 before a live API is available. The commands read `TODO.md` and store transient claim/heartbeat state in `.agent-workbench/bootstrap-state.json` (git-ignored). Set `AGENT_WORKBENCH_BOOTSTRAP_STATE=/path/to/state.json` to override the state path for tests or runners.

## Go CLI Commands (Phase 2+, API must be running)

```bash
awb task next
awb task list --status pending
awb task claim <id> --agent opencode
awb task heartbeat <id> --agent opencode
awb task complete <id> --agent opencode
awb task block <id> --agent opencode --reason "blocked on X"
awb status show --project <slug>
awb project list
```

Add `--output json` to any command for machine-readable output.

## Bootstrap Script Commands (Phase 1, Markdown-backed)

```bash
./scripts/task-next --json
./scripts/task-claim todo:L55 --agent opencode --note "starting work"
./scripts/task-heartbeat todo:L55 --note "still working"
./scripts/task-complete todo:L55 --note "implemented and validated"
./scripts/task-block todo:L55 --note "blocked on missing credential"
./scripts/status-show --json
```

**One command per call.** Run each script as its own standalone shell invocation. Do not chain them with `&&`, `;`, or pipe them together. The Claude Code permission rule `Bash(./scripts/*)` matches the full command string — a compound like `./scripts/task-claim … && echo done` will not match and will prompt for approval unnecessarily.

## Transition Roadmap

The bootstrap commands are intentionally stable even while their implementation changes.

| Phase | Backing store | Status | Goal | Exit criteria |
| --- | --- | --- | --- | --- |
| 1. Markdown + local state | `TODO.md`, `MEMORY.md`, `.agent-workbench/bootstrap-state.json` | **Done** | Give OpenCode and humans a usable command shape immediately. | Commands return predictable JSON and agents still update Markdown handoff files. |
| 2. API-backed CLI/scripts | Flask API + PostgreSQL + `awb` Go CLI | **In progress** | Replace ignored local state with durable task/status/runs/events records. | `awb task next/claim/heartbeat/complete/block` and `awb status show` all call the API and append events. |
| 3. Full coordination workflow | API + Go CLI + generated Markdown summaries | Planned | Make Postgres/API the coordination source of truth while preserving concise handoff files. | A test project can run an agent task loop without direct Markdown edits for primary state. |
| 4. Human review UI | API + CLI + web UI | Post-MVP | Add browser workflows for review, ad hoc task entry, and signoff. | Web UI covers project/task/review inspection without changing the agent-facing contracts. |

The scripts should remain thin wrappers once the Go CLI exists. Keep their output compatible with scheduled OpenCode usage unless a replacement command is documented first.

## Overnight OpenCode Flow

When the API is running (Phase 2+), prefer `awb`:

1. `awb status show --project <slug>`
2. `awb task next`
3. `awb task claim <id> --agent opencode`
4. Run OpenCode for one focused task.
5. `awb task heartbeat <id> --agent opencode` during longer work.
6. `awb task complete <id> --agent opencode` or `awb task block <id> --agent opencode --reason "..."`.

When the API is not yet running (Phase 1 fallback), use the bootstrap scripts instead:

1. `./scripts/status-show --json`
2. `./scripts/task-next --json`
3. `./scripts/task-claim <task-id> --agent opencode`
4. Run OpenCode for one focused task.
5. `./scripts/task-heartbeat <task-id>` during longer work.
6. `./scripts/task-complete <task-id>` or `./scripts/task-block <task-id> --note "..."`.

In either case, agents must still update `TODO.md`, `MEMORY.md`, docs, and tests according to `AGENTS.md` and `AGENT_WORKFLOW.md` before claiming implementation is done.
