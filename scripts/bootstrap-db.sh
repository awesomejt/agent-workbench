#!/usr/bin/env bash
# Bootstrap the agent_workbench schema against a target environment.
# This is safe to run multiple times — the SQL uses IF NOT EXISTS.
#
# Usage:
#   ./scripts/bootstrap-db.sh --env local
#   ./scripts/bootstrap-db.sh --env dev     # requires AGENT_WORKBENCH_DEV_DATABASE_URL
#   ./scripts/bootstrap-db.sh --env stage   # requires AGENT_WORKBENCH_STAGE_DATABASE_URL
#   ./scripts/bootstrap-db.sh --env prod    # requires AGENT_WORKBENCH_PROD_DATABASE_URL
#
# For local, DATABASE_URL is read from api/.env (must exist).
# For non-local, supply the URL via the environment variable for the target env.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="${REPO_ROOT}/db/bootstrap/create-schema.sql"
ENV_FILE="${REPO_ROOT}/api/.env"
APP_ENV="local"

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      APP_ENV="$2"
      shift 2
      ;;
    *)
      echo "Usage: $0 --env local|dev|stage|prod" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$SQL_FILE" ]]; then
  echo "ERROR: SQL file not found: $SQL_FILE" >&2
  exit 1
fi

# Resolve DATABASE_URL for the target environment
case "$APP_ENV" in
  local)
    if [[ ! -f "$ENV_FILE" ]]; then
      echo "ERROR: api/.env not found. Copy api/.env.example to api/.env and fill in values." >&2
      exit 1
    fi
    # Read DATABASE_URL from .env (ignore comments and blank lines)
    RAW_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
    if [[ -z "$RAW_URL" ]]; then
      echo "ERROR: DATABASE_URL not found in api/.env" >&2
      exit 1
    fi
    ;;
  dev)
    RAW_URL="${AGENT_WORKBENCH_DEV_DATABASE_URL:-}"
    if [[ -z "$RAW_URL" ]]; then
      echo "ERROR: AGENT_WORKBENCH_DEV_DATABASE_URL is not set" >&2
      exit 1
    fi
    ;;
  stage)
    RAW_URL="${AGENT_WORKBENCH_STAGE_DATABASE_URL:-}"
    if [[ -z "$RAW_URL" ]]; then
      echo "ERROR: AGENT_WORKBENCH_STAGE_DATABASE_URL is not set" >&2
      exit 1
    fi
    ;;
  prod)
    RAW_URL="${AGENT_WORKBENCH_PROD_DATABASE_URL:-}"
    if [[ -z "$RAW_URL" ]]; then
      echo "ERROR: AGENT_WORKBENCH_PROD_DATABASE_URL is not set" >&2
      exit 1
    fi
    echo ""
    echo "WARNING: Targeting PRODUCTION database. Press Ctrl+C within 5 seconds to abort."
    sleep 5
    ;;
  *)
    echo "ERROR: Unknown env '${APP_ENV}'. Valid values: local, dev, stage, prod" >&2
    exit 1
    ;;
esac

# Strip SQLAlchemy driver prefix (e.g., postgresql+psycopg:// → postgresql://)
PSQL_URL="$(echo "$RAW_URL" | sed 's|+[a-zA-Z0-9_]*://|://|')"

echo "Bootstrapping schema for env=${APP_ENV}..."
psql "$PSQL_URL" -f "$SQL_FILE"
echo "Done."
