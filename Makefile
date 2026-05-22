.PHONY: help setup up down db-up db-down migrate migrate-dev migrate-stage migrate-prod \
        lint format type-check test smoke validate build-cli \
        task-next status-show clean

API_DIR = api

# Default target
help:
	@echo "Agent Workbench — available targets:"
	@echo ""
	@echo "  Local development (Docker Compose):"
	@echo "    setup         Install Python dependencies via uv (inside api/)"
	@echo "    up            Start db service"
	@echo "    down          Stop and remove containers"
	@echo "    db-up         Start only the database container"
	@echo "    db-down       Stop the database container"
	@echo "    migrate             Run Alembic migrations against local db (uses api/.env)"
	@echo "    migrate-generate    Generate a new migration: make migrate-generate MSG=\"description\""
	@echo ""
	@echo "  Non-local migrations (require DATABASE_URL env var to be set externally):"
	@echo "    migrate-dev   Run migrations against dev (APP_ENV=dev)"
	@echo "    migrate-stage Run migrations against stage (APP_ENV=stage)"
	@echo "    migrate-prod  Run migrations against prod (APP_ENV=prod) — prompts for confirmation"
	@echo ""
	@echo "  Code quality:"
	@echo "    lint          Run ruff linter (inside api/)"
	@echo "    format        Run ruff formatter check (inside api/)"
	@echo "    type-check    Run mypy type checker (inside api/)"
	@echo "    validate      Validate Python syntax and imports"
	@echo "    test          Run pytest (inside api/)"
	@echo "    smoke         Run curl smoke checks against running API"
	@echo ""
	@echo "  CLI:"
	@echo "    build-cli     Build Go CLI into cli/builds/ (stub until cli/ is scaffolded)"
	@echo ""
	@echo "  Bootstrap scripts (local Markdown-backed state):"
	@echo "    task-next     Show next available AI Agent Work task"
	@echo "    status-show   Show bootstrap state summary"
	@echo ""
	@echo "  Cleanup:"
	@echo "    clean         Remove generated files and Docker volumes"

# ── Dependencies ──────────────────────────────────────────────────────────────

setup:
	cd $(API_DIR) && uv sync

# ── Docker Compose services ───────────────────────────────────────────────────

up: db-up

db-up:
	docker compose up -d db

db-down:
	docker compose stop db

down:
	docker compose down

# ── Database migrations ───────────────────────────────────────────────────────

migrate:
	cd $(API_DIR) && uv run --env-file .env alembic upgrade head

migrate-generate:
	cd $(API_DIR) && uv run --env-file .env alembic revision --autogenerate -m "$(MSG)"

migrate-dev:
	@test -n "$(AGENT_WORKBENCH_DEV_DATABASE_URL)" || \
		(echo "ERROR: AGENT_WORKBENCH_DEV_DATABASE_URL is not set" && exit 1)
	cd $(API_DIR) && APP_ENV=dev DATABASE_URL=$(AGENT_WORKBENCH_DEV_DATABASE_URL) uv run alembic upgrade head

migrate-stage:
	@test -n "$(AGENT_WORKBENCH_STAGE_DATABASE_URL)" || \
		(echo "ERROR: AGENT_WORKBENCH_STAGE_DATABASE_URL is not set" && exit 1)
	cd $(API_DIR) && APP_ENV=stage DATABASE_URL=$(AGENT_WORKBENCH_STAGE_DATABASE_URL) uv run alembic upgrade head

migrate-prod:
	@test -n "$(AGENT_WORKBENCH_PROD_DATABASE_URL)" || \
		(echo "ERROR: AGENT_WORKBENCH_PROD_DATABASE_URL is not set" && exit 1)
	@echo "WARNING: About to migrate PRODUCTION database. Press Ctrl+C within 5 seconds to abort."
	@sleep 5
	cd $(API_DIR) && APP_ENV=prod DATABASE_URL=$(AGENT_WORKBENCH_PROD_DATABASE_URL) uv run alembic upgrade head

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	cd $(API_DIR) && uv run ruff check src/

format:
	cd $(API_DIR) && uv run ruff format --check src/

type-check:
	cd $(API_DIR) && uv run mypy src/

validate:
	python3 -m py_compile scripts/awb.py
	cd $(API_DIR) && uv run python -c "from agent_workbench.app import create_app; print('imports ok')"

test:
	cd $(API_DIR) && uv run --env-file .env pytest

smoke:
	@./scripts/smoke-curl.sh 2>/dev/null || echo "smoke-curl.sh not yet implemented"

# ── CLI ───────────────────────────────────────────────────────────────────────

build-cli:
	@mkdir -p cli/builds
	@which go > /dev/null 2>&1 || (echo "ERROR: go not found in PATH" && exit 1)
	@echo "Go CLI scaffold not yet added — see TODO: Scaffold Go CLI command tree"

# ── Bootstrap scripts (local Markdown state) ──────────────────────────────────

task-next:
	./scripts/task-next --json

status-show:
	./scripts/status-show --json

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(API_DIR)/.pytest_cache $(API_DIR)/.mypy_cache $(API_DIR)/.ruff_cache
