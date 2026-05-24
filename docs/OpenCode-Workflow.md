# OpenCode Automation Workflow

Describes how OpenCode scheduled runs integrate with the Agent Workbench for
unattended, task-driven development sessions.

## Overview

`scripts/opencode-run.sh` is the workbench-native wrapper for unattended
OpenCode runs. It:

1. Calls `awb task next` to claim the highest-priority pending task.
2. Builds a focused, task-specific prompt that includes the task ID, title,
   phase, and exact `awb` lifecycle commands.
3. Invokes `opencode run --dir <repo>` with that prompt.
4. The OpenCode agent reads the prompt, does the work, and calls
   `awb task complete` or `awb task block` before exiting.

This is different from the general `afk-run.sh` approach (see
[opencode-setup](file:///shared/projects/ai/opencode-setup)) which sends a
discovery prompt and lets the agent choose its own task. `opencode-run.sh`
pre-selects one task so the agent stays focused.

## Quick Start

```bash
# Ensure the API is running and awb CLI is built
make db-up
make build-cli
# (start the API separately — see docs/Development.md)

# Dry-run: see which task would be claimed and the full prompt
AWB_API_URL=http://localhost:8000 \
AWB_PROJECT=agent-workbench \
AWB_AGENT=opencode \
make opencode-run -- --dry-run

# Live run
AWB_API_URL=http://localhost:8000 \
AWB_PROJECT=agent-workbench \
AWB_AGENT=opencode \
OPENCODE_MODEL=omlx1/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-6bit \
make opencode-run
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AWB_API_URL` | `http://localhost:8000` | Agent Workbench API base URL |
| `AWB_PROJECT` | `agent-workbench` | Project slug |
| `AWB_AGENT` | `opencode` | Agent name reported to the workbench |
| `OPENCODE_MODEL` | *(opencode default)* | Model ID passed to `opencode run` |
| `OPENCODE_AGENT` | `yolo` | OpenCode agent profile |
| `OPENCODE_DRY_RUN` | `0` | Set to `1` to print prompt without running |
| `OPENCODE_LOG_FILE` | *(stderr only)* | Path to append log output |

## Task Lifecycle Inside the Agent

The prompt tells the agent exactly which task it is working on and supplies the
full `awb` command with env vars pre-filled:

```
export AWB_API_URL=... AWB_PROJECT=... AWB_AGENT=...
AWB=/path/to/cli/builds/awb

# Renew lease every few minutes
$AWB task heartbeat <task-id> --agent opencode

# On success
$AWB task complete <task-id> --agent opencode --evidence "<summary>"

# If blocked
$AWB task block <task-id> --agent opencode --reason "<reason>"
```

The agent is responsible for calling one of those before it exits. If the
agent crashes without completing, the lease expires naturally (default: 30
minutes) and the task becomes available again for the next run.

## Lock File

`opencode-run.sh` uses an atomic `mkdir` lock at
`/tmp/opencode-run-<repo-key>.lock` to prevent overlapping runs. If a run is
already active, the script exits 0 immediately. The lock is removed on EXIT,
INT, and TERM signals.

Override the lock path with `OPENCODE_LOCK_DIR`.

## Scheduling

### systemd timer (recommended)

Create `~/.config/systemd/user/opencode-run.service`:

```ini
[Unit]
Description=Agent Workbench — OpenCode task runner

[Service]
Type=oneshot
WorkingDirectory=/shared/projects/dev/agent-workbench
Environment=AWB_API_URL=http://localhost:8000
Environment=AWB_PROJECT=agent-workbench
Environment=AWB_AGENT=opencode
Environment=OPENCODE_MODEL=omlx1/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-6bit
Environment=OPENCODE_LOG_FILE=%h/.local/share/agent-workbench/opencode-run.log
ExecStart=/shared/projects/dev/agent-workbench/scripts/opencode-run.sh
```

Create `~/.config/systemd/user/opencode-run.timer`:

```ini
[Unit]
Description=Run OpenCode task loop every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable:

```bash
systemctl --user daemon-reload
systemctl --user enable --now opencode-run.timer
```

### cron

```cron
*/5 * * * * AWB_API_URL=http://localhost:8000 AWB_PROJECT=agent-workbench AWB_AGENT=opencode \
  OPENCODE_MODEL=... OPENCODE_LOG_FILE=~/.local/share/agent-workbench/opencode-run.log \
  /shared/projects/dev/agent-workbench/scripts/opencode-run.sh
```

## Relationship to opencode-setup

`opencode-setup` (`/shared/projects/ai/opencode-setup`) provides the general
`afk-run.sh` runner, which can target any repository and sends a discovery
prompt. It now detects the `awb` CLI and the bootstrap scripts when they are
present.

`opencode-run.sh` (this repo) is the workbench-specific wrapper that pre-selects
one task and builds a focused prompt. Use it when running against
`agent-workbench` directly. Use `afk-run.sh` when running against other repos
that consume the workbench API.

## Debugging

```bash
# See the exact prompt without running opencode
OPENCODE_DRY_RUN=1 ./scripts/opencode-run.sh --dry-run --verbose

# Check which task would be selected
AWB_API_URL=http://localhost:8000 AWB_PROJECT=agent-workbench \
  cli/builds/awb task next --output json

# Tail log output
tail -f ~/.local/share/agent-workbench/opencode-run.log
```
