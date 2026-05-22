# Technical Stack

Document the approved tools, languages, frameworks, libraries, and versions for this project.

## Runtime And Language

- API language/runtime: Python 3.14 latest.
- Package manager: `uv` preferred.
- Database runtime: PostgreSQL 18. Do not use SQLite.
- CLI language/runtime: Go 1.26.
- CLI libraries: Cobra and Viper.
- Web language/runtime: Node.js 24 LTS with latest npm.
- Local orchestration: Docker Engine with Docker Compose v2.
- Deployment target: Docker Compose VM first; K3s deployment is a future feature.

## Frameworks And Libraries

- API framework: Flask.
- Database access: SQLAlchemy 2.x plus Alembic migrations is the default recommendation unless another stack is chosen.
- PostgreSQL driver: psycopg 3.x preferred for new Python work.
- CLI/bootstrap: initial stub commands for OpenCode, then a Go 1.26 CLI using Cobra and Viper, managed by Makefile.
- CLI build output: `cli/builds/`, excluded from Git.
- Testing:
  - Unit tests for state machines and validation.
  - API tests for route contracts.
  - PostgreSQL-backed integration tests.
  - Curl smoke checks for quick human feedback.
  - Python containerized integration tests for agent workflows.
- Web UI: post-MVP; defer until API/CLI bootstrap is stable enough for a test project.
- Web UI framework/runtime: React client with Node.js 24 LTS, latest npm, and Express for web-server/API proxy integration where needed.
- Observability: optional Prometheus metrics endpoint, likely `/metrics`, enabled by configuration.
- Authentication: deferred for private-network MVP; future IDP integration should be researched before broader exposure.

## Repository Structure

The repository is organized as a monorepo with three top-level component directories:

```
api/        Python/Flask API — package managed by uv, pyproject.toml, alembic.ini, migrations/
cli/        Go CLI — Cobra/Viper, builds to cli/builds/ (stub until scaffolded)
web/        React web UI — Node.js 24 LTS, npm, Express (post-MVP stub)
scripts/    Bootstrap agent scripts (Markdown-backed local state, MVP interim tools)
db/         Database bootstrap SQL (schema creation templates)
```

Root-level files (`docker-compose.yml`, `Makefile`) orchestrate all components.

## Commands

Primary dev workflow uses Docker Compose for services and `make` targets from the repo root:

```bash
# Install API Python dependencies (inside api/)
make setup

# Start database container
make db-up                          # or: docker compose up -d db

# Run Alembic migrations against local db via Docker Compose
make migrate                        # docker compose --profile migrate run --rm migrations

# Start API server via Docker Compose (api profile)
docker compose --profile api up api

# Bootstrap agent workflow (Markdown-backed, interim until CLI is ready)
make status-show
make task-next
./scripts/task-claim <task-id> --agent opencode
./scripts/task-heartbeat <task-id>
./scripts/task-complete <task-id>
./scripts/task-block <task-id> --note "blocked reason"

# Code quality (runs inside api/)
make lint
make format
make type-check
make validate

# Run tests (inside api/)
make test

# Run curl smoke checks against running API
make smoke

# Build Go CLI (stub until cli/ is scaffolded)
make build-cli

# Stop everything and clean volumes
make clean
```

Root `Makefile` wraps all the above with `API_DIR = api` prefix for Python targets.

## Environment

- Required API environment variables:
  - `DATABASE_URL`: active PostgreSQL connection URL.
  - `APP_ENV`: `local`, `dev`, `stage`, or `prod`.
  - `API_HOST` and `API_PORT`: optional local bind settings.
  - `PROMETHEUS_ENABLED`: optional flag for metrics endpoint exposure.
- Optional database URL variables for bootstrap scripts:
  - `AGENT_WORKBENCH_LOCAL_DATABASE_URL`
  - `AGENT_WORKBENCH_DEV_DATABASE_URL`
  - `AGENT_WORKBENCH_STAGE_DATABASE_URL`
  - `AGENT_WORKBENCH_PROD_DATABASE_URL`
- Local services:
  - PostgreSQL container managed by Docker Compose.
- Dev/stage/production:
  - Use separate PostgreSQL hosts: `postgresql-dev`, `postgresql-stage`, and `postgresql`/`postgresql.taylor.lan`.
  - Initial non-local deployment can use Docker Compose env files or Compose secrets.
  - HashiCorp Vault exists in the homelab and should be investigated later, not required for MVP.
  - Production host is expected to be `postgresql` on the LAN and/or `postgresql.taylor.lan`.
  - Use `agent_workbench` as the stable schema name unless Jason confirms separate schema names per environment.
  - Database credentials must come from deployment secrets, not Git.
- Ansible:
  - Secrets may exist on the Ansible host under `~/projects/infra/ansible/vars/common/secrets.yaml`.
  - Agents must not read or copy secret values into this repo.

## Version Notes

- Target **major.minor** versions (e.g., Flask 3.x, SQLAlchemy 2.x, Go 1.26, Node.js 24 LTS). Patch versions are managed automatically by uv (Python), go modules (CLI), and npm (web).
- CachyOS/rolling distributions deliver latest packages; use dependency managers rather than pinning patch versions manually.
- Use stable releases; avoid experimental/canary packages for the coordination core.
- Known installed package versions from scaffolding run: Flask 3.1, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0, Alembic 1.18, psycopg 3.3, pydantic-settings 2.14, Python 3.14.5.
