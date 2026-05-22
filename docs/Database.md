# Database Plan

`Agent Workbench` should use PostgreSQL as the source of truth for agent coordination state once the bootstrap schema and tooling exist.

## Environments

Use one explicit environment flag everywhere:

- `APP_ENV=local` - local development using a Docker Compose PostgreSQL container.
- `APP_ENV=dev` - shared development database for separated testing.
- `APP_ENV=stage` - staging database for release-candidate validation.
- `APP_ENV=prod` - production database, expected on `postgresql.taylor.lan`.

Deployed runtime should default to `prod` once the system is in real use. Local commands, tests, and Make targets must set `APP_ENV=local` explicitly so local work never accidentally talks to production.

CLI/scripts should also accept an explicit `--env local|dev|stage|prod` flag when practical. Destructive or administrative commands should require explicit confirmation when `APP_ENV=prod`.

## Connection Variables

Preferred variables:

- `APP_ENV`: selected environment.
- `DATABASE_URL`: active SQLAlchemy/PostgreSQL connection URL for the selected environment.
- `AGENT_WORKBENCH_LOCAL_DATABASE_URL`: optional local override.
- `AGENT_WORKBENCH_DEV_DATABASE_URL`: optional dev override.
- `AGENT_WORKBENCH_STAGE_DATABASE_URL`: optional stage override.
- `AGENT_WORKBENCH_PROD_DATABASE_URL`: optional prod override.

Runtime code should resolve `DATABASE_URL` first. Bootstrap scripts may resolve the environment-specific variable from `APP_ENV` and then export or pass it as `DATABASE_URL`.

## Target Databases And Schemas

Preferred layout:

| Environment | PostgreSQL target | Database | Schema |
| --- | --- | --- | --- |
| local | Docker Compose container | `agent_workbench` | `agent_workbench` |
| dev | shared dev PostgreSQL | `agent_workbench_dev` | `agent_workbench` |
| stage | shared stage PostgreSQL | `agent_workbench_stage` | `agent_workbench` |
| prod | `postgresql.taylor.lan` | `agent_workbench_prod` | `agent_workbench` |

Use separate databases or hosts per environment where available. Keep the schema name stable as `agent_workbench` so migrations are environment-independent.

If the existing PostgreSQL layout uses one database per server and separate schemas instead, use these schema names instead:

- `agent_workbench_local`
- `agent_workbench_dev`
- `agent_workbench_stage`
- `agent_workbench_prod`

Choose one layout before migrations are finalized and record the decision in `MEMORY.md`.

## Secret Handling

- Do not commit database credentials or complete database URLs.
- Ansible secrets are expected under `~/projects/infra/ansible/vars/common/secrets.yaml` on the Ansible host.
- Agents may reference that path as an operational source, but must not read, copy, summarize, or commit secret values.
- Deployment should inject the correct database URL through environment variables, Docker Compose secrets, K3s secrets, or Ansible-managed env files.

## Module/Section And Phase Model

Projects can contain zero or more modules/sections. Use a first-class table such as `project_sections` rather than encoding module names only in free text.

Recommended fields for `project_sections`:

- `id`
- `project_id`
- `name`
- `slug`
- `section_type` such as `module`, `section`, `chapter`, `lesson`, `article_section`, or `area`
- `description`
- `sort_order`
- `metadata`
- `created_at`, `updated_at`, `version`

Status records and tasks should include:

- `project_id`
- nullable `project_section_id`
- `phase`

Use `project_section_id = null` for project-wide/general work. Do not require a special `general` section row unless a later UI or reporting need makes that useful.

Initial phase values:

- `planning`
- `research`
- `implementation`
- `testing`
- `review`

## Migration Policy

- Alembic or the selected migration tool should own schema creation and upgrades.
- The same migrations should run against local, dev, stage, and prod.
- Local development can recreate the container database freely.
- Dev/stage/prod migrations require explicit `APP_ENV` and should be logged.
- Production migrations should be part of a documented release procedure and run only after stage validation.

## Bootstrap Setup Tasks

Initial database setup should create empty target databases/schemas and then let migrations create tables. Use `db/bootstrap/create-schema.sql` when a target database exists but the `agent_workbench` schema has not yet been created.

Example non-secret flow:

```bash
# Local container
APP_ENV=local docker compose up -d db
APP_ENV=local uv run alembic upgrade head

# Shared environments, with secrets supplied externally
APP_ENV=dev DATABASE_URL="$AGENT_WORKBENCH_DEV_DATABASE_URL" uv run alembic upgrade head
APP_ENV=stage DATABASE_URL="$AGENT_WORKBENCH_STAGE_DATABASE_URL" uv run alembic upgrade head
APP_ENV=prod DATABASE_URL="$AGENT_WORKBENCH_PROD_DATABASE_URL" uv run alembic upgrade head
```

Do not run dev/stage/prod commands until secret injection and target database names are confirmed.

## Project Discovery Roots

Existing local projects live under `~/projects` with logical groupings:

- `~/projects/ai`
- `~/projects/courses`
- `~/projects/dev`
- `~/projects/infra`

The Ansible project lives at `~/projects/infra/ansible`.

Project import/discovery should treat these as configurable roots, not hard-coded assumptions. The first project scanner can use these defaults for Jason's environment while allowing overrides through config.
