# Bootstrap CLI

These commands give OpenCode and humans a stable local interface before the real PostgreSQL/API/Go CLI workflow exists.

The commands read `TODO.md` and store transient claim/heartbeat state in `.agent-workbench/bootstrap-state.json`, which is ignored by Git. Set `AGENT_WORKBENCH_BOOTSTRAP_STATE=/path/to/state.json` to override the state path for tests or runners. This avoids committing noisy coordination updates while preserving a command shape that can later be replaced by the real CLI/API.

## Commands

```bash
./scripts/task-next --json
./scripts/task-claim todo:L55 --agent opencode --note "starting work"
./scripts/task-heartbeat todo:L55 --note "still working"
./scripts/task-complete todo:L55 --note "implemented and validated"
./scripts/task-block todo:L55 --note "blocked on missing credential"
./scripts/status-show --json
```

## Transition Roadmap

The bootstrap commands are intentionally stable even while their implementation changes.

| Phase | Backing store | Goal | Exit criteria |
| --- | --- | --- | --- |
| 1. Markdown + local state | `TODO.md`, `MEMORY.md`, `.agent-workbench/bootstrap-state.json` | Give OpenCode and humans a usable command shape immediately. | Commands return predictable JSON and agents still update Markdown handoff files. |
| 2. API-backed CLI/scripts | Flask API + PostgreSQL | Replace ignored local state with durable task/status/runs/events records. | `task-next`, claim, heartbeat, complete, block, and status-show all call the API and append events. |
| 3. Full coordination workflow | API + Go CLI + generated Markdown summaries | Make Postgres/API the coordination source of truth while preserving concise handoff files. | A test project can run an agent task loop without direct Markdown edits for primary state. |
| 4. Human review UI | API + CLI + web UI | Add browser workflows for review, ad hoc task entry, and signoff. | Web UI covers project/task/review inspection without changing the agent-facing contracts. |

The scripts should remain thin wrappers once the Go CLI exists. Keep their output compatible with scheduled OpenCode usage unless a replacement command is documented first.

## Overnight OpenCode Flow

A scheduled OpenCode run can use this rough flow:

1. `./scripts/status-show --json`
2. `./scripts/task-next --json`
3. `./scripts/task-claim <task-id> --agent opencode`
4. Run OpenCode for one focused task.
5. `./scripts/task-heartbeat <task-id>` during longer work.
6. `./scripts/task-complete <task-id>` or `./scripts/task-block <task-id> --note "..."`.

Until the real database-backed CLI exists, agents must still update `TODO.md`, `MEMORY.md`, docs, and tests according to `AGENTS.md` and `AGENT_WORKFLOW.md` before claiming implementation is done.
