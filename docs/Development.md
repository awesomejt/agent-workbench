# Development Guide

Local setup, daily workflow, and environment reference for Agent Workbench contributors and agents.

For deploying to dev/stage/prod, see [Deployment.md](Deployment.md).

## Prerequisites

| Tool | Required version | Install |
|---|---|---|
| Docker Engine + Compose v2 | Latest stable | distro package or Docker Desktop |
| Go | 1.26+ | distro package or `go.dev/dl` |
| Python | 3.14+ | distro package or `pyenv` |
| `uv` | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `pg_isready` | Any (from `postgresql-client`) | distro package |

`awb` itself is built from this repo — no separate install needed.

## First-Time Setup

```bash
# Clone
git clone git@github.com:awesomejt/agent-workbench.git
cd agent-workbench

# Install Python dependencies
make setup                  # cd api && uv sync

# Configure local env (copy template, no changes needed for local dev)
cp api/.env.example api/.env

# Start the database container (PostgreSQL 18 on localhost:5433)
make db-up

# Run schema migrations
make migrate

# Build the CLI
make build-cli              # writes cli/builds/awb

# Optional: install awb system-wide
make install-cli            # installs to ~/.local/bin or ~/bin
```

## Running the API

**Option 1 — direct (recommended for development):**

```bash
cd api && uv run --env-file .env agent-workbench-api
```

The server binds to `http://localhost:8000` by default. `Ctrl+C` to stop.

**Option 2 — Docker Compose profile:**

```bash
docker compose --profile api up api
```

This builds and runs the API container. Useful for testing the Docker build path.

Check that the API is up: `curl http://localhost:8000/health`

## Daily Development Workflow

```bash
make db-up                  # ensure DB is running (idempotent)
make test                   # run pytest (exits with hint if DB is unreachable)
make lint                   # ruff lint
make format                 # ruff format check
make type-check             # mypy
make validate               # all three quality checks in one command
make build-cli              # rebuild awb after CLI changes
make cli-vet                # go vet
make cli-test               # go test ./...
```

## CLI Config

Avoid repeating `--project` and `--agent` on every command by creating a config file:

```yaml
# ~/.config/awb/config.yaml
api_url: http://localhost:8000
project: agent-workbench
agent: claude-sonnet-4-6
```

The CLI also reads environment variables with the `AWB_` prefix:

| Variable | CLI flag equivalent | Default |
|---|---|---|
| `AWB_API_URL` | `--api-url` | `http://localhost:8000` |
| `AWB_PROJECT` | `--project` | _(none)_ |
| `AWB_AGENT` | `--agent` | _(none)_ |
| `AWB_OUTPUT` | `--output` | `table` |

## Shell Completion

```bash
# Fish (recommended — auto-loaded)
awb completion fish > ~/.config/fish/completions/awb.fish

# Bash
awb completion bash > /etc/bash_completion.d/awb
# or: source <(awb completion bash)

# Zsh
awb completion zsh > "${fpath[1]}/_awb"
```

## Running Tests

```bash
make test
# Equivalent: cd api && uv run --env-file .env pytest
```

`make test` runs a `pg_isready` pre-check and prints an actionable hint if the container is not reachable. Tests use a separate `agent_workbench_test` database defined in `api/.env` (`AGENT_WORKBENCH_TEST_DATABASE_URL`).

## Database

### Local container

Managed by Docker Compose. The `db_data` Docker volume persists across restarts.

```bash
make db-up          # start container (localhost:5433)
make db-down        # stop container (data preserved)
make clean          # docker compose down -v (destroys volume — wipes all data)
```

### Migrations

```bash
make migrate                        # upgrade local db to latest
make migrate-generate MSG="desc"    # generate a new revision from model diff
```

Non-local environments require an explicit `DATABASE_URL` env var — never infer non-local credentials from the repo:

```bash
# Dev
AGENT_WORKBENCH_DEV_DATABASE_URL=... make migrate-dev

# Stage
AGENT_WORKBENCH_STAGE_DATABASE_URL=... make migrate-stage

# Prod (5-second abort window)
AGENT_WORKBENCH_PROD_DATABASE_URL=... make migrate-prod
```

### Seed local data

Populate the local database with project/section/task records from `TODO.md` state:

```bash
make seed-dev       # idempotent — safe to re-run
```

The script is at `scripts/seed_dev.py`. It uses the Flask app context directly (no running API needed) and skips records that already exist by slug/title.

## Environment Variables

### API

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection URL (`postgresql+psycopg://…`) |
| `APP_ENV` | Yes | `local`, `dev`, `stage`, or `prod` |
| `SECRET_KEY` | No (auto-generated locally) | Flask secret key; required in prod and must not be the default |
| `API_HOST` | No | Bind address (default `127.0.0.1`) |
| `API_PORT` | No | Bind port (default `8000`) |
| `PROMETHEUS_ENABLED` | No | Enable `/metrics` endpoint (default `false`) |

Copy `api/.env.example` to `api/.env`. For local development the defaults work as-is.

### CLI

| Variable | Description |
|---|---|
| `AWB_API_URL` | API base URL (default `http://localhost:8000`) |
| `AWB_PROJECT` | Default project slug |
| `AWB_AGENT` | Default agent name for task operations |
| `AWB_OUTPUT` | Output format: `table` (default) or `json` |

### Makefile / migrations

| Variable | Description |
|---|---|
| `AGENT_WORKBENCH_DEV_DATABASE_URL` | Used by `make migrate-dev` |
| `AGENT_WORKBENCH_STAGE_DATABASE_URL` | Used by `make migrate-stage` |
| `AGENT_WORKBENCH_PROD_DATABASE_URL` | Used by `make migrate-prod` |
| `POSTGRES_PASSWORD` | Docker Compose DB password (default `agent_workbench_local`) |
| `DB_PORT` | Host port for PostgreSQL container (default `5433`) |
| `API_PORT` | Host port for API container (default `8000`) |

## Project Structure

```
api/
  src/agent_workbench/    Flask application package
    app.py                application factory
    config.py             pydantic-settings config
    database.py           SQLAlchemy db instance
    errors.py             error handler registration
    projects/             projects module (models, routes, service)
    project_sections/     sections module
    project_status/       status module
    tasks/                tasks module (incl. lease mechanics)
    agents/               agents module
    runs/                 runs module
    events/               events module (append-only)
    reviews/              reviews module
  tests/                  pytest test suite
  migrations/             Alembic migration scripts
  pyproject.toml
  alembic.ini
cli/
  cmd/                    Cobra command files (one per resource)
  internal/
    api/                  HTTP client + type definitions
    render/               table and JSON output helpers
  main.go
scripts/
  install-awb.sh          installs awb to ~/.local/bin or ~/bin
  seed_dev.py             seeds local DB from TODO.md state
  smoke-curl.sh           curl smoke checks
  task-{next,claim,...}   Markdown-backed bootstrap scripts (Phase 1 fallback)
docs/
  API-Contracts.md        canonical REST contract (routes, errors, pagination)
  Architecture.md         ERD and module boundaries
  Database.md             schema, environment targets, migration strategy
  Bootstrap-CLI.md        transition roadmap (Markdown → API → full coordination)
  Tech-Stack.md           approved tools, versions, and commands reference
  Development.md          (this file)
```

## Dogfood Workflow

Agent Workbench manages its own remaining tasks. Use `awb` to interact with them during development:

```bash
# See what's pending
awb task list --project agent-workbench --status pending

# Pick up a task
awb task next --project agent-workbench
awb task claim <id> --agent claude-sonnet-4-6

# Record a run
awb run start --project agent-workbench --task <id> --summary "implementing X"
awb run heartbeat <run-id>

# Finish
awb task complete <id> --agent claude-sonnet-4-6
awb run complete <run-id> --summary "done"
```

During the dogfood transition, `TODO.md` remains the authoritative human-readable record. Update both `awb` (via CLI) and `TODO.md` when completing tasks, until the workflow is fully validated.

## Code Quality Gates

```bash
make validate       # ruff check + ruff format --check + mypy (all must pass)
make test           # pytest (all tests must pass)
make cli-vet        # go vet (must pass before any CLI commit)
make cli-test       # go test ./... (must pass)
```

`make cli-clean-build-check` runs a clean-clone build from `git archive` to catch `.gitignore` issues before they affect CI.

## Secrets Policy

- Never commit `.env`, credentials, private keys, or database URLs.
- `api/.env.example` is the template — it contains no secrets.
- Non-local database URLs must be injected at runtime via environment variables or Compose secrets.
- Ansible secrets at `~/projects/infra/ansible/vars/common/secrets.yaml` must never be copied into this repo.
- `APP_ENV` and `DATABASE_URL` are the safety boundary — do not guess or synthesize non-local values.
