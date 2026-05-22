# Database Bootstrap

This folder contains non-secret database bootstrap helpers.

## Files

- `create-schema.sql` - creates the `agent_workbench` schema and `pgcrypto` extension in the currently selected database.

## Usage

Use only after selecting the correct environment and supplying credentials outside Git.

```bash
# Local container example
APP_ENV=local psql "$DATABASE_URL" -f db/bootstrap/create-schema.sql

# Shared environment examples, with secrets supplied externally
APP_ENV=dev psql "$AGENT_WORKBENCH_DEV_DATABASE_URL" -f db/bootstrap/create-schema.sql
APP_ENV=stage psql "$AGENT_WORKBENCH_STAGE_DATABASE_URL" -f db/bootstrap/create-schema.sql
APP_ENV=prod psql "$AGENT_WORKBENCH_PROD_DATABASE_URL" -f db/bootstrap/create-schema.sql
```

Production bootstrap should happen through a documented release/deployment workflow after stage validation.
