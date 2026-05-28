# Deployment Guide

How to deploy Agent Workbench to dev, stage, or production environments.

For local development setup, see [Development.md](Development.md).

---

## Prerequisites

| Component | Requirement |
|---|---|
| PostgreSQL | 18+, accessible from the deployment host |
| Docker Engine + Compose v2 | For container-based deployment |
| Python 3.14+ + `uv` | If running the API directly (non-container) |
| `psql` client | For schema bootstrap |
| Secrets manager | Ansible, `pass`, `direnv`, CI/CD secrets — any that keeps credentials out of Git |

---

## Environment Targets

| `APP_ENV` | PostgreSQL host | Database | Schema |
|---|---|---|---|
| `local` | Docker Compose (`localhost:5433`) | `agent_workbench` | `agent_workbench` |
| `dev` | `postgresql-dev` | `agent_workbench` | `agent_workbench` |
| `stage` | `postgresql-stage` | `agent_workbench` | `agent_workbench` |
| `prod` | `postgresql` / `postgresql.taylor.lan` | `agent_workbench` | `agent_workbench` |

All environments use the same database name `agent_workbench` and schema `agent_workbench`. Isolation is by host, not by database name.

---

## Database Setup

This is a two-step process: bootstrap the schema (once per environment), then run Alembic migrations.

### Step 1 — Create the database and user

Run this on the target PostgreSQL host (or via `psql` with superuser credentials). Replace `<password>` with the value from your secrets manager.

```sql
CREATE USER awb WITH PASSWORD '<password>';
CREATE DATABASE agent_workbench OWNER awb;
```

The PostgreSQL user is `awb` (not `agent_workbench`). The database name is `agent_workbench` in all environments.

If the database already exists but the `agent_workbench` schema does not, skip to Step 2.

### Step 2 — Bootstrap the schema

The bootstrap script creates the `agent_workbench` schema and the `pgcrypto` extension. It is safe to run multiple times (`IF NOT EXISTS`).

Supply the connection URL as an environment variable, then run:

```bash
# Dev
AGENT_WORKBENCH_DEV_DATABASE_URL="postgresql+psycopg://awb:<pass>@postgresql-dev/agent_workbench" \
  make bootstrap-db-dev

# Stage
AGENT_WORKBENCH_STAGE_DATABASE_URL="postgresql+psycopg://awb:<pass>@postgresql-stage/agent_workbench" \
  make bootstrap-db-stage

# Prod — includes a 5-second abort window
AGENT_WORKBENCH_PROD_DATABASE_URL="postgresql+psycopg://awb:<pass>@postgresql.taylor.lan/agent_workbench" \
  make bootstrap-db-prod
```

**Note:** if the password contains special characters (e.g. `@`), percent-encode them in the URL: `@` → `%40`. Example: `Mytric@01` → `Mytric%4001`.

The bootstrap SQL is at [db/bootstrap/create-schema.sql](../db/bootstrap/create-schema.sql). It contains no credentials.

### Step 3 — Run migrations

After the schema exists, apply all Alembic migrations:

```bash
# Dev
AGENT_WORKBENCH_DEV_DATABASE_URL="..." make migrate-dev

# Stage
AGENT_WORKBENCH_STAGE_DATABASE_URL="..." make migrate-stage

# Prod (5-second abort window)
AGENT_WORKBENCH_PROD_DATABASE_URL="..." make migrate-prod
```

Migrations run from the `api/` directory against the schema created in Step 2. The same migrations apply across all environments — there are no environment-specific branches.

**Verify:**

```bash
psql "$DATABASE_URL" -c "\dt agent_workbench.*"
```

You should see tables: `agents`, `ai_servers`, `events`, `idempotency_keys`, `projects`, `project_sections`, `project_statuses`, `reviews`, `runs`, `tasks`, `task_relationships`.

---

## API Deployment

### Required environment variables

| Variable | Required | Notes |
|---|---|---|
| `APP_ENV` | Yes | `dev`, `stage`, or `prod` |
| `DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@host/dbname` |
| `SECRET_KEY` | Yes (non-local) | Run `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `API_HOST` | No | Bind address (default `127.0.0.1`; use `0.0.0.0` for containers) |
| `API_PORT` | No | Bind port (default `8000`) |
| `PROMETHEUS_ENABLED` | No | Set `true` to expose `/metrics` |

`SECRET_KEY` must be set to a strong random value in all non-local environments. The API will refuse to start with the development default.

### Option A — Docker Compose

Create a secrets file outside the repo (never in Git):

```bash
# /etc/agent-workbench/env  (on the deployment host)
APP_ENV=prod
DATABASE_URL=postgresql+psycopg://awb:<pass>@postgresql.taylor.lan/agent_workbench
SECRET_KEY=<strong-random-hex>
API_HOST=0.0.0.0
API_PORT=8000
```

Then run:

```bash
docker compose --env-file /etc/agent-workbench/env --profile api up -d api
```

The `api` profile builds the image from `api/` and starts the container. The `db` service is not started — point `DATABASE_URL` at your external PostgreSQL instance.

To run migrations via Compose before starting the API:

```bash
docker compose --env-file /etc/agent-workbench/env --profile migrate run --rm migrations
docker compose --env-file /etc/agent-workbench/env --profile api up -d api
```

### Option B — Direct (systemd or process manager)

```bash
cd /opt/agent-workbench/api
APP_ENV=prod \
DATABASE_URL="postgresql+psycopg://..." \
SECRET_KEY="..." \
API_HOST="0.0.0.0" \
  uv run agent-workbench-api
```

A minimal systemd unit (`/etc/systemd/system/agent-workbench-api.service`):

```ini
[Unit]
Description=Agent Workbench API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/agent-workbench/api
EnvironmentFile=/etc/agent-workbench/env
ExecStart=uv run agent-workbench-api
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now agent-workbench-api
```

### Health check

```bash
curl http://<host>:8000/health
# {"status": "ok"}
```

---

## CLI Configuration

Point the `awb` CLI at your deployed API:

```yaml
# ~/.config/awb/config.yaml
api_url: http://<host>:8000
project: agent-workbench
agent: <your-agent-name>
```

Or via environment variables:

```bash
export AWB_API_URL=http://<host>:8000
export AWB_PROJECT=agent-workbench
```

Build and install the CLI locally — it connects to the API over HTTP, so no deployment of the CLI binary itself is needed on the server:

```bash
make install-cli    # installs awb to ~/.local/bin or ~/bin
```

---

## AI Server Probe (Optional)

The probe script checks registered AI servers and updates their `status` field in the API. Run it on a schedule from any host that can reach both the Agent Workbench API and your AI servers:

```bash
# Manual run
AWB_API_URL=http://<host>:8000 python3 /opt/agent-workbench/scripts/probe-ai-servers.py

# Cron — every 5 minutes
*/5 * * * * AWB_API_URL=http://<host>:8000 PROBE_TIMEOUT=5 /usr/bin/python3 /opt/agent-workbench/scripts/probe-ai-servers.py >> /var/log/agent-workbench-probe.log 2>&1
```

Register AI servers first:

```bash
# Example: register a local Ollama server
curl -s -X POST http://<host>:8000/api/ai-servers \
  -H "Content-Type: application/json" \
  -d '{"name": "homelab-ollama-1", "url": "http://192.168.1.100:11434", "server_type": "ollama"}'
```

After the probe runs, `GET /api/ai-servers?available=true` returns only servers currently `up`.

---

## Upgrading

1. Pull the new code.
2. Run migrations against the target environment (Step 3 above).
3. Restart the API container or process.

```bash
git pull
AGENT_WORKBENCH_PROD_DATABASE_URL="..." make migrate-prod
docker compose --env-file /etc/agent-workbench/env --profile api up -d --build api
```

Always run migrations before restarting the API — the new code expects the new schema.

---

## Secrets Policy

- Never commit `.env`, credentials, database URLs, or `SECRET_KEY` values.
- Obtain non-local database URLs from Ansible (`~/projects/infra/ansible/vars/common/secrets.yaml`) or your secrets manager.
- Agents must not read or copy values from Ansible secrets into this repo.
- See [Secrets.md](Secrets.md) for the full policy and future Vault integration plan.
