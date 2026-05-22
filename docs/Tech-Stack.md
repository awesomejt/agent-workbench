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

## Commands

Initial target commands after scaffolding:

```bash
# Install dependencies
uv sync

# Start local services
docker compose up -d db

# Run migrations
uv run alembic upgrade head

# Run API locally
uv run agent-workbench-api

# Bootstrap agent workflow examples
make status-show
make task-next
./scripts/task-claim <task-id> --agent opencode
./scripts/task-heartbeat <task-id>
./scripts/task-complete <task-id>
./scripts/task-block <task-id> --note "blocked reason"

# Build CLI once scaffolded (Go + Cobra/Viper)
make build-cli

# Build and run web once post-MVP web work is scheduled
make web-install
make web-dev

# Run tests
uv run pytest

# Run smoke checks
./scripts/smoke-curl.sh

# Run containerized integration tests
docker compose run --rm integration-test
```

Root `Makefile` targets should wrap these once implemented.

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

- Verify current Python 3.14 patch, PostgreSQL 18 patch, Flask, SQLAlchemy, Alembic, psycopg, Go 1.26, Cobra, Viper, Node.js 24 LTS, npm latest, Express, and Prometheus client library versions before scaffolding related modules.
- Use stable releases; avoid experimental/canary packages for the coordination core.
