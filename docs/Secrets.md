# Secret Handling

How Agent Workbench manages credentials across local, dev, stage, and production environments.

## Guiding Principles

- No secrets are committed to Git, ever.
- `api/.env.example` contains only placeholder values — copy it to `api/.env` and fill in real values locally.
- Database URLs and passwords are injected at runtime via environment variables or Docker Compose secrets.
- `APP_ENV` and `DATABASE_URL` are the safety boundary: never guess or synthesize non-local values.
- Ansible secrets at `~/projects/infra/ansible/vars/common/secrets.yaml` must never be copied into this repo.

## Local Development

Copy the template and edit with your local values:

```bash
cp api/.env.example api/.env
```

The defaults in `.env.example` work as-is for local development:

| Variable | Local default |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://agent_workbench:agent_workbench_local@localhost:5433/agent_workbench` |
| `APP_ENV` | `local` |
| `SECRET_KEY` | auto-generated (safe to omit locally) |

`api/.env` is listed in `.gitignore`. Never commit it.

## Docker Compose env files

For the API container, pass secrets via an env file:

```yaml
# compose.yaml (api service, --profile api)
services:
  api:
    env_file: api/.env
```

For dev/stage deployment on a VM, supply a secrets file at deploy time and reference it in Compose:

```bash
docker compose --env-file /run/secrets/agent-workbench.env up -d
```

Keep the secrets file outside the repo — on the VM filesystem, in a mounted secret, or in a CI/CD secret variable.

## Non-local Migrations

Non-local database URLs must be injected explicitly and are never stored in the repo:

```bash
# Dev
AGENT_WORKBENCH_DEV_DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db" make migrate-dev

# Stage
AGENT_WORKBENCH_STAGE_DATABASE_URL="..." make migrate-stage

# Prod (5-second abort window)
AGENT_WORKBENCH_PROD_DATABASE_URL="..." make migrate-prod
```

These env vars are not set in any committed file. Inject them from your shell, CI/CD secrets, or a tool like `pass` or `direnv` with a gitignored `.envrc`.

## Docker Compose Secrets (future)

For production Compose deployments, Docker Compose native secrets provide better isolation than env files:

```yaml
secrets:
  db_password:
    file: /run/secrets/db_password

services:
  api:
    secrets:
      - db_password
    environment:
      DATABASE_URL: "postgresql+psycopg://user:${DB_PASSWORD}@host:5432/db"
```

The secrets file lives outside the repo on the deployment host. This is the intended path after initial VM deployment is validated.

## SECRET_KEY

Flask requires a `SECRET_KEY` for session signing. Behavior by environment:

| `APP_ENV` | Behavior |
|---|---|
| `local` | Auto-generated at startup if not set (safe for local dev) |
| `dev` / `stage` / `prod` | **Required** — startup fails if it matches the development default |

Set a strong random value in non-local environments:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Ansible Integration

Production host configuration (including database passwords, host names, and deployment parameters) lives in Ansible at `~/projects/infra/ansible/vars/common/secrets.yaml`.

Agents must not read from that path or copy values into this repo. If a deployment requires credentials from Ansible, Jason runs the playbook — agents do not.

## HashiCorp Vault (Future)

Vault integration is planned for post-MVP use to provide dynamic secrets, audit logging, and lease management for database credentials. The pattern will be:

1. Vault generates short-lived PostgreSQL credentials on demand.
2. The API container receives `DATABASE_URL` via Vault Agent Sidecar or direct API call at startup.
3. Compose secrets are replaced by Vault-injected env vars.

Until Vault is set up, Docker Compose env files and Ansible-managed secrets are the injection mechanism.
