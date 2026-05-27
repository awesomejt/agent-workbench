.PHONY: help setup up down db-up db-down \
        bootstrap-db bootstrap-db-dev bootstrap-db-stage bootstrap-db-prod \
        migrate migrate-dev migrate-stage migrate-prod \
        lint format type-check test integration-test smoke validate build-cli cli-tidy cli-vet install-cli \
        cli-test cli-clean-build-check probe-servers task-next status-show seed-dev opencode-run \
        web-install web-dev web-build onboard onboard-archive install-onboard clean

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
	@echo "    bootstrap-db        Create agent_workbench schema + pgcrypto on local db (idempotent)"
	@echo "    bootstrap-db-dev    Create schema on dev (requires AGENT_WORKBENCH_DEV_DATABASE_URL)"
	@echo "    bootstrap-db-stage  Create schema on stage (requires AGENT_WORKBENCH_STAGE_DATABASE_URL)"
	@echo "    bootstrap-db-prod   Create schema on prod — prompts for confirmation"
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
	@echo "    integration-test  Build and run containerized integration tests (Docker required)"
	@echo "    smoke         Run curl smoke checks against running API"
	@echo "    probe-servers Probe all registered AI servers and update availability status"
	@echo ""
	@echo "  CLI:"
	@echo "    build-cli     Build Go CLI binary to cli/builds/awb"
	@echo "    cli-tidy      Run go mod tidy for the CLI module"
	@echo "    cli-vet       Run go vet on the CLI"
	@echo "    install-cli   Build and install awb to ~/.local/bin or ~/bin"
	@echo "    cli-test      Run Go CLI tests"
	@echo "    cli-clean-build-check  Build CLI from git archive to catch gitignore issues"
	@echo ""
	@echo "  Onboarding:"
	@echo "    onboard         Process ready project/task files in onboarding/"
	@echo "                    AWB_API_URL overrides http://localhost:8000"
	@echo "                    ONBOARD_DRY_RUN=1 previews without changes"
	@echo "    onboard-archive Move processed files to onboarding/archive/"
	@echo "                    ONBOARD_DRY_RUN=1 previews without moving"
	@echo "    install-onboard Install awb-onboard/awb-onboard-archive stubs"
	@echo "                    INSTALL_DIR, ONBOARDING_DIR, AWB_API_URL control the install"
	@echo ""
	@echo "  OpenCode integration:"
	@echo "    opencode-run  Claim next workbench task and run one focused OpenCode session"
	@echo "                  Uses AWB_API_URL, AWB_PROJECT, AWB_AGENT env vars."
	@echo "                  Pass --dry-run to preview without invoking opencode."
	@echo ""
	@echo "  Web UI (post-MVP):"
	@echo "    web-install   Install npm dependencies (web/)"
	@echo "    web-dev       Start Vite dev server (port 3000, proxies /api to localhost:8000)"
	@echo "    web-build     Build production bundle to web/dist/"
	@echo "                  Docker Compose profile 'web' runs the production Express server."
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

# ── Schema bootstrap ─────────────────────────────────────────────────────────

bootstrap-db:
	@./scripts/bootstrap-db.sh --env local

bootstrap-db-dev:
	@./scripts/bootstrap-db.sh --env dev

bootstrap-db-stage:
	@./scripts/bootstrap-db.sh --env stage

bootstrap-db-prod:
	@./scripts/bootstrap-db.sh --env prod

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
	cd $(API_DIR) && uv run ruff check src/
	cd $(API_DIR) && uv run ruff format --check src/
	cd $(API_DIR) && uv run mypy src/

test:
	@pg_isready -h localhost -p 5433 -q 2>/dev/null || \
		(echo "Hint: PostgreSQL not reachable on localhost:5433. Run 'make db-up' to start the database container." && exit 1)
	cd $(API_DIR) && uv run --env-file .env pytest

integration-test:
	docker compose -p agent-workbench-itest -f compose.integration.yaml up --build -d; \
	RUNNER=""; \
	while [ -z "$$RUNNER" ]; do \
		sleep 2; \
		RUNNER=$$(docker compose -p agent-workbench-itest -f compose.integration.yaml ps -q test-runner 2>/dev/null); \
	done; \
	docker logs -f $$RUNNER; \
	CODE=$$(docker wait $$RUNNER); \
	docker compose -p agent-workbench-itest -f compose.integration.yaml down -v; \
	exit $$CODE

smoke:
	@./scripts/smoke-curl.sh 2>/dev/null || echo "smoke-curl.sh not yet implemented"

probe-servers:
	AWB_API_URL=http://localhost:8000 python3 scripts/probe-ai-servers.py

# ── CLI ───────────────────────────────────────────────────────────────────────

CLI_DIR = cli
CLI_BIN = cli/builds/awb

build-cli:
	@mkdir -p cli/builds
	@which go > /dev/null 2>&1 || (echo "ERROR: go not found in PATH" && exit 1)
	cd $(CLI_DIR) && go build -o builds/awb .
	@echo "built: $(CLI_BIN)"

cli-tidy:
	cd $(CLI_DIR) && go mod tidy

cli-vet:
	cd $(CLI_DIR) && go vet ./...

install-cli: build-cli
	@./scripts/install-awb.sh

cli-test:
	cd $(CLI_DIR) && go test ./...

cli-clean-build-check:
	@echo "Checking clean-clone build from git archive..."
	@tmp=$$(mktemp -d) && \
	  git archive HEAD cli/ | tar -x -C $$tmp && \
	  cd $$tmp/cli && go build ./... && \
	  echo "clean-clone build: ok" && \
	  rm -rf $$tmp

# ── Onboarding ───────────────────────────────────────────────────────────────

onboard:
	uv run scripts/onboard.py \
		--onboarding-dir onboarding/ \
		--api-url $(or $(AWB_API_URL),http://localhost:8000) \
		$(if $(ONBOARD_DRY_RUN),--dry-run)

onboard-archive:
	uv run scripts/onboard.py \
		--onboarding-dir onboarding/ \
		--archive \
		$(if $(ONBOARD_DRY_RUN),--dry-run)

install-onboard:
	@[ -n "$(INSTALL_DIR)" ]     || (echo "error: INSTALL_DIR is required"; exit 1)
	@[ -n "$(ONBOARDING_DIR)" ]  || (echo "error: ONBOARDING_DIR is required"; exit 1)
	bash scripts/install-onboard.sh \
		--install-dir "$(INSTALL_DIR)" \
		--onboarding-dir "$(ONBOARDING_DIR)" \
		$(if $(AWB_API_URL),--api-url "$(AWB_API_URL)")

# ── OpenCode integration ──────────────────────────────────────────────────────

opencode-run:
	@./scripts/opencode-run.sh

# ── Web UI ───────────────────────────────────────────────────────────────────

WEB_DIR = web

web-install:
	cd $(WEB_DIR) && npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

web-build:
	cd $(WEB_DIR) && npm run build

# ── Seed ─────────────────────────────────────────────────────────────────────

seed-dev:
	cd $(API_DIR) && uv run --env-file .env python ../scripts/seed_dev.py

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
