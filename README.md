# Agent Workbench

A PostgreSQL-backed API and CLI for coordinating AI agent work across Git projects. Agents claim tasks, record heartbeats, append events, and complete runs — all durably stored and queryable, replacing per-repo Markdown noise with a shared coordination layer.

## Status

**Early dogfood.** The Flask API, PostgreSQL schema, and `awb` CLI are operational. All pre-dogfood fixes (P0–P3) are complete. Agent Workbench is now managing its own remaining development tasks.

## Quick Start

```bash
# 1. Start the database
make db-up

# 2. Install Python dependencies
make setup

# 3. Run migrations
make migrate

# 4. Build and install the CLI
make install-cli        # installs awb to ~/.local/bin or ~/bin

# 5. Start the API (separate terminal)
cd api && uv run --env-file .env agent-workbench-api
```

The API binds to `http://localhost:8000` by default. Check `GET /health` to confirm it's up.

See [docs/Development.md](docs/Development.md) for a full walkthrough including config, environment variables, and the Docker Compose API profile. For deploying to dev/stage/prod, see [docs/Deployment.md](docs/Deployment.md).

## CLI Usage

```bash
# Project and task discovery
awb project list
awb task list --project <slug>
awb task next --project <slug>          # next available (unlocked) pending task

# Agent task lifecycle
awb task claim   <id> --agent <name>
awb task heartbeat <id> --agent <name>
awb task complete  <id> --agent <name>
awb task block     <id> --agent <name> --reason "why"

# Run records (one run per agent session)
awb run start --project <slug> [--task <id>] [--summary "goal"]
awb run heartbeat <run-id>
awb run complete  <run-id> [--summary "outcome"]
awb run fail      <run-id> [--summary "what failed"]

# Audit trail
awb event list --project <slug>
awb status show --project <slug>

# Administration
awb agent list
awb section list --project <slug>
```

Add `--output json` to any command for machine-readable output.

Configure defaults so you don't repeat `--project` and `--agent` every time:

```yaml
# ~/.config/awb/config.yaml
api_url: http://localhost:8000
project: agent-workbench
agent: claude-sonnet-4-6
```

Or via environment variables: `AWB_API_URL`, `AWB_PROJECT`, `AWB_AGENT`.

## Project Structure

```
api/        Python/Flask API — uv, pyproject.toml, Alembic migrations
cli/        Go CLI (awb) — Cobra/Viper, builds to cli/builds/
web/        React web UI — post-MVP stub
scripts/    Bootstrap scripts (Markdown-backed fallback) + install-awb.sh + seed_dev.py
docs/       Architecture, API contracts, database, bootstrap, and stack notes
db/         Schema bootstrap SQL templates
```

## API Modules

| Module | Routes | Purpose |
|---|---|---|
| `projects` | `GET/POST /api/projects`, `GET/PATCH /api/projects/<id>` | Project registry |
| `project_sections` | `/api/projects/<id>/sections` | Sections/modules within a project |
| `project_status` | `/api/projects/<id>/status` | Status history per project/section |
| `tasks` | `/api/projects/<id>/tasks`, `/api/tasks/<id>/…` | Tasks, leases, lifecycle |
| `agents` | `/api/agents` | Agent registry |
| `runs` | `/api/runs` | Agent session run records |
| `events` | `/api/projects/<id>/events`, `POST /api/events` | Append-only audit trail |
| `reviews` | `/api/projects/<id>/reviews` | Cloud review findings and signoff |

Full contract details: [docs/API-Contracts.md](docs/API-Contracts.md).

## Architecture Principles

- One modular Flask monolith, one PostgreSQL database — no microservices at this stage.
- Git is the source of truth for source code; PostgreSQL is the source of truth for coordination state.
- Optimistic locking (`version` field) on all mutable resources.
- Atomic task claiming via targeted `UPDATE … WHERE id = ? AND claimed_until < now()` with rowcount check.
- Append-only events table — no update or delete routes on events.
- `APP_ENV=local|dev|stage|prod`; deployed runtime defaults to `prod`.

## Development

See [docs/Development.md](docs/Development.md) for full setup, testing, environment variables, and migration workflows.

```bash
make validate       # ruff lint + format + mypy
make test           # pytest (requires DB on localhost:5433)
make smoke          # curl smoke checks against running API
make build-cli      # rebuild awb binary
make seed-dev       # seed local DB from TODO.md state (idempotent)
```

## Task Onboarding

Human operators can author tasks as Markdown files and have them automatically ingested into the workbench inbox.

1. Copy `onboarding/task.template.md` to a new file in `onboarding/` (any name, e.g. `onboarding/my-task.md`).
2. Fill in the front matter (`title`, `project`, `phase`, `role`, `model_tier`, `priority`) and write the task description in the body.
3. Set `status: ready` when the task is complete.

```bash
make onboard            # process all ready files (requires API on localhost:8000)
ONBOARD_DRY_RUN=1 make onboard   # preview without creating tasks
AWB_API_URL=http://... make onboard   # override API URL
```

The tool sets `status: processed` and adds `task_id` + `processed_at` to the file's front matter after a task is created. Files with `status: draft` and `*.template.md` files are ignored.

To run automatically, add a cron entry:

```
*/30 * * * * cd /path/to/agent-workbench && make onboard
```

## Bootstrap Fallback

During Phase 1 (before a live API), bootstrap scripts back agent commands with Markdown files:

```bash
./scripts/task-next --json
./scripts/task-claim <id> --agent opencode
./scripts/task-heartbeat <id>
./scripts/task-complete <id>
```

These remain available as a fallback. See [docs/Bootstrap-CLI.md](docs/Bootstrap-CLI.md) for the full transition roadmap.
