#!/usr/bin/env python3
"""Seed the local dev database with agent-workbench project data from TODO.md.

Usage (from repo root):
    cd api && uv run --env-file .env python ../scripts/seed_dev.py

Idempotent: skips project/section/task creation if a record with the same
slug or title already exists.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../api/src"))

from sqlalchemy import select

from agent_workbench.app import create_app
from agent_workbench.database import db
from agent_workbench.projects.models import Project
from agent_workbench.project_sections.models import ProjectSection
from agent_workbench.tasks.models import Task
from agent_workbench.projects import service as projects_service
from agent_workbench.project_sections import service as sections_service
from agent_workbench.tasks import service as tasks_service

# ── Project ───────────────────────────────────────────────────────────────────

PROJECT_DATA = {
    "name": "Agent Workbench",
    "slug": "agent-workbench",
    "project_type": "service",
    "environment": "local",
    "local_path": "/shared/projects/dev/agent-workbench",
    "git_remote_url": "git@github.com:awesomejt/agent-workbench.git",
    "default_agent": "claude-sonnet-4-6",
}

# ── Sections ──────────────────────────────────────────────────────────────────

SECTIONS = [
    {
        "name": "Needs Attention",
        "slug": "needs-attention",
        "sort_order": 10,
        "description": (
            "Items requiring Jason's input, a decision, credentials, external access, "
            "or manual validation before agent work can continue."
        ),
    },
    {
        "name": "Manual Validation",
        "slug": "manual-validation",
        "sort_order": 20,
        "description": (
            "Items needing Jason to validate on real systems, live services, devices, "
            "accounts, or deployment targets."
        ),
    },
    {
        "name": "AI Review",
        "slug": "ai-review",
        "sort_order": 30,
        "description": (
            "Cloud-based AI review tasks: contract map, stale-doc comparison, "
            "implementation review, and pre-dogfood fix tracking."
        ),
    },
    {
        "name": "Pre-Dogfood Fixes",
        "slug": "pre-dogfood-fixes",
        "sort_order": 40,
        "description": (
            "Items required before using agent-workbench to manage its own development. "
            "Ordered P0 (build-breaking) → P3 (CLI expansion)."
        ),
    },
    {
        "name": "Discovery and Planning",
        "slug": "discovery-planning",
        "sort_order": 50,
        "description": "Research, planning, framework decisions, and early discovery tasks.",
    },
    {
        "name": "Architecture and Contracts",
        "slug": "architecture-contracts",
        "sort_order": 60,
        "description": "API contracts, data models, schema decisions, and architectural patterns.",
    },
    {
        "name": "Scaffolding",
        "slug": "scaffolding",
        "sort_order": 70,
        "description": (
            "Build tooling, Docker Compose, CI targets, and project infrastructure setup."
        ),
    },
    {
        "name": "Core API Modules",
        "slug": "core-api-modules",
        "sort_order": 80,
        "description": "Flask API module implementation: projects, tasks, runs, events, agents, reviews.",
    },
    {
        "name": "Tests and Quality",
        "slug": "tests-quality",
        "sort_order": 90,
        "description": "Test suites, quality gates, lint/format/type-check tooling.",
    },
    {
        "name": "Documentation and Deployment",
        "slug": "docs-deployment",
        "sort_order": 100,
        "description": "README, deployment docs, operational notes, and migration guides.",
    },
]

# ── Tasks ─────────────────────────────────────────────────────────────────────
# Each entry: (title, status, phase, completion_evidence_or_None)
# P0/P1 are marked completed based on git log (da937e6, f98cc15) even though
# TODO.md still shows [ ] — those checkboxes were not updated after the fixes landed.

TASKS: dict[str, list[tuple[str, str, str, str | None]]] = {
    "needs-attention": [
        (
            "Confirm API framework: Flask",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm MVP starts with API plus CLI/scripts; web UI is post-MVP for human review and ad hoc task entry",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm private-network MVP can defer authentication; research IDP before wider exposure",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm exact dev/stage/production database names and users; initial secret injection direction is Docker Compose env files/secrets with Vault as future research",
            "pending", "planning", None,
        ),
        (
            "Confirm OpenCode scheduled runs should use stub CLI commands during bootstrap, with gradual replacement by real CLI/API",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm deployed runtime should default to APP_ENV=prod while local/test commands explicitly select APP_ENV=local",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm shared PostgreSQL environments use separate servers/databases with same schema agent_workbench",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Confirm deployment target order: Docker Compose VM first, K3s later as future feature",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
    ],
    "manual-validation": [
        ("Confirm requirements and success criteria in PROJECT_BRIEF.md", "pending", "review", None),
        ("Confirm chosen stack and deployment target", "pending", "review", None),
        (
            "Confirm credentials, API keys, database URLs, and production access are not committed",
            "pending", "review", None,
        ),
        ("Validate local PostgreSQL container startup after Compose is added", "pending", "testing", None),
        (
            "Validate dev/stage database connectivity when secrets are available",
            "pending", "testing", None,
        ),
        ("Validate target schema/database creation in dev and stage", "pending", "testing", None),
        (
            "Validate production postgresql.taylor.lan connectivity during release readiness",
            "pending", "testing", None,
        ),
        (
            "Validate target schema/database creation in prod during release readiness",
            "pending", "testing", None,
        ),
        (
            "Validate deployment or release workflow on the target environment",
            "pending", "testing", None,
        ),
    ],
    "ai-review": [
        (
            "Cloud review: build a current contract map for API routes, request/response JSON, error shapes, CLI/script commands, database schema, Docker services, environment variables, and build outputs",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: compare docs, source, tests, Docker/Compose, README, and TODO for stale or conflicting contracts",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: inspect data model for task leases, heartbeats, idempotency, optimistic locking, event history, and multi-project support",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: inspect API implementation for correctness, validation gaps, transaction/session lifecycle, error consistency, and PostgreSQL assumptions",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: inspect bootstrap CLI/scripts for safe task claiming, useful diagnostics, and stable agent-facing output",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: inspect Docker/Compose and deployment docs for repeatability and secret handling",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Cloud review: run or specify the closest available validation commands and record failures, skipped checks, and missing tooling",
            "completed", "review",
            "Completed 2026-05-22 by Codex; ruff lint passes, ruff format fails (15 files), mypy fails (17 errors), pytest passes (54 tests), go vet passes, clean-clone build fails due to gitignore issue.",
        ),
        (
            "Cloud review: convert findings into prioritized TODO items before broad refactoring begins",
            "completed", "review",
            "Completed 2026-05-22 by Codex; findings recorded in docs/reviews/2026-05-22-1741-codex-cli-repo-recommendations.md and added to pre-dogfood fix list.",
        ),
        (
            "Cloud review signoff: confirm all high-risk findings are resolved or explicitly deferred before real use",
            "pending", "review", None,
        ),
    ],
    "pre-dogfood-fixes": [
        # P0 — committed in da937e6 (TODO.md [ ] not updated after fix)
        (
            "P0: Fix .gitignore global output/ rule silently ignoring cli/internal/output/output.go; rename directory to cli/internal/render and update all import paths",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6; renamed cli/internal/output to cli/internal/render.",
        ),
        (
            "P0: Fix CLI nil pointer dereference: task_claim.go dereferences *task.ClaimedBy without a nil check; crashes on any unassigned task",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.",
        ),
        (
            "P0: Fix CLI double-error printing: commands return err to Cobra while also calling output.Err; results in duplicate error messages on stderr",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.",
        ),
        (
            "P0: Trim trailing slashes from --api-url in the API client to prevent malformed URLs like http://host//api/...",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit da937e6.",
        ),
        # P1 — committed in f98cc15 (TODO.md [ ] not updated after fix)
        (
            "P1: Run ruff format across all Python source files (15 files currently fail format check); add format check to make validate",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.",
        ),
        (
            "P1: Fix 17 mypy errors; decide and document mypy strictness policy for Flask-SQLAlchemy and rowcount typing patterns; add make type-check to make validate",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.",
        ),
        (
            "P1: Make awb task next and awb task list lease-aware: add available=true API filter meaning status=pending AND (claimed_until IS NULL OR claimed_until < now()); update CLI flags accordingly",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.",
        ),
        (
            "P1: Fix root/.env.example.local to use port 5433 and password agent_workbench_local to match api/.env.example and Docker Compose",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 in commit f98cc15.",
        ),
        # P2 — committed in 63769db
        (
            "P2: Auto-append events on task lifecycle transitions (claim, heartbeat, complete, block) within the same DB transaction as the state change; add tests",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; events/service._record() helper; 5 new tests in test_tasks.py.",
        ),
        (
            "P2: Auto-append events on run transitions (heartbeat, complete, fail) within the same DB transaction; add tests",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; 4 new tests in test_runs.py.",
        ),
        (
            "P2: Define and implement idempotency behavior: scope to endpoint + actor + key rather than a single task column; update API and CLI to send and replay idempotency keys on claim/heartbeat/complete/block",
            "pending", "implementation", None,
        ),
        (
            "P2: Add API validation: duration_seconds must be a positive integer within a reasonable range; return 422 on invalid input",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; 1-604800s range enforced in claim and heartbeat routes.",
        ),
        (
            "P2: Add API validation: project_section_id on tasks must belong to the same project; return 422 on mismatch",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; validated on task create and update.",
        ),
        (
            "P2: Add API validation: task_id on run creation must belong to the provided project; return 422 on mismatch",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; project existence and task ownership validated in runs/routes.py.",
        ),
        (
            "P2: Add enum validation for task status, phase, review status, and review severity fields; return 422 with field-level error details",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; frozenset constants in tasks/routes.py and reviews/routes.py; 5 new tests.",
        ),
        (
            "P2: Decide and document whether task block should clear the lease like task complete does, or hold it intentionally; implement and test the chosen behavior",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; decision: block clears lease (agent gives up the task; it stays blocked until reset to pending); 1 new test confirms claimed_by/claimed_until both null after block.",
        ),
        (
            "P2: Add make cli-test target (cd cli && go test ./...); add make cli-clean-build-check target that builds from a git archive to catch future gitignore issues",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6 (P0/P1 session).",
        ),
        (
            "P2: Add a friendly hint to make test when the local PostgreSQL container is not reachable",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; pg_isready pre-check with actionable message.",
        ),
        # P3 — committed in e99f69b
        (
            "P3: Add awb run start/get/heartbeat/complete/fail commands so every agent session can create a durable run record and heartbeat through it",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
        (
            "P3: Add awb event list/append commands for debugging and audit trail inspection",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; event list supports --limit, append accepts --type/--task/--run/--actor-name/--payload.",
        ),
        (
            "P3: Add awb agent list/create/get/update commands for agent registry management",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
        (
            "P3: Add awb project create/get/update and awb section list/create/get/update commands for project and section administration",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
        (
            "P3: Add awb status create/update commands for project/section status management from the CLI",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; status show now includes ID column for use with update.",
        ),
        (
            "P3: Add shell completion (awb completion bash/zsh/fish/powershell) with inline install instructions",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
    ],
    "discovery-planning": [
        (
            "Bootstrap project direction, workflow docs, and planning files for Agent Workbench",
            "completed", "planning",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Replace template placeholders with Agent Workbench project direction",
            "completed", "planning",
            "Completed 2026-05-22.",
        ),
        (
            "Clarify that agent-workbench is the active work target and project-status is reference material only",
            "completed", "planning",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Inventory reusable lessons from /shared/projects/dev/project-status without copying known implementation drift",
            "completed", "planning",
            "Completed 2026-05-22 by Copilot.",
        ),
        (
            "Inventory OpenCode setup repo requirements from /shared/projects/ai/opencode-setup",
            "completed", "planning",
            "Completed 2026-05-22 by OpenCode.",
        ),
        (
            "Decide initial API framework: Python 3.14 latest plus Flask",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Decide initial CLI stack: Go 1.26 with Cobra and Viper",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Decide post-MVP web stack: React with Node.js 24 LTS, latest npm, and Express",
            "completed", "planning",
            "Completed 2026-05-22 by Jason.",
        ),
        (
            "Decide Flask package layout",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; src/ layout, application factory, Flask-SQLAlchemy 3.x, pydantic-settings, per-module blueprints inside api/.",
        ),
        (
            "Define initial module boundaries: projects, project_sections, status, tasks, agents, runs, events, reviews",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; modules scaffolded with models, routes, and service stubs.",
        ),
        (
            "Define initial API route style and compatibility policy without URL versioning by default",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; documented in docs/API-Contracts.md (no URL versioning, canonical routes, pagination, error shape).",
        ),
        (
            "Define initial database schema and migration strategy, including task assignee/owner fields",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; 8 SQLAlchemy models with UUID PKs, optimistic locking, lease fields on tasks, append-only events; Alembic configured in api/.",
        ),
        (
            "Define local/dev/stage/prod database target names and stable schema policy in docs/Database.md",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; DB targets, schema agent_workbench, and env var names documented in docs/Database.md.",
        ),
        (
            "Define bootstrap transition from Markdown files to Postgres-backed scripts/CLI/API",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; docs/Bootstrap-CLI.md now describes Markdown/local state, API-backed scripts, full CLI coordination, and post-MVP web phases.",
        ),
        (
            "Evaluate Grok planning/scaffolding review for worthwhile recommendations",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; accepted centralized API contract doc, additional Mermaid diagrams, bootstrap transition roadmap, and impact-weighted task selection guidance.",
        ),
        (
            "Dogfood: register agent-workbench as its own project in the workbench once pre-dogfood fixes are done; use awb to manage all remaining implementation tasks instead of editing TODO.md directly",
            "pending", "planning", None,
        ),
        (
            "Define project discovery config for ~/projects/ai, ~/projects/courses, ~/projects/dev, and ~/projects/infra",
            "pending", "planning", None,
        ),
        (
            "Define project type vocabulary, default sections/modules, phase workflows, and default agent selection rules",
            "pending", "planning", None,
        ),
        (
            "Define state machines for project status, task status, agent run status, and review findings",
            "pending", "planning", None,
        ),
        (
            "Define task assignee/owner model for agent and human responsibility",
            "pending", "planning", None,
        ),
        (
            "Define task duration estimation model: t-shirt sizing (XS/S/M/L/XL) or Agile story points mapped to seconds, with agent-capability multipliers (cloud vs. local AI) so lease windows auto-scale without manual estimated_duration_seconds on every task",
            "pending", "planning", None,
        ),
        (
            "Define status/task event history strategy, including bootstrap structured logging before full event APIs if needed",
            "pending", "planning", None,
        ),
        (
            "Define optional Prometheus metrics scope, config flag, endpoint, and deployment notes for prometheus.taylor.lan",
            "pending", "planning", None,
        ),
        (
            "Add runtime metrics fields to runs table: model_id, prompt_tokens, completion_tokens, latency_ms, prompt_category — to inform lease duration tuning and model selection heuristics",
            "pending", "planning", None,
        ),
        (
            "Create benchmark-harness as a separate project: structured AI agent evaluation with prompt libraries, scoring rubrics, and comparison reports; consumes agent-workbench API as infrastructure",
            "pending", "planning", None,
        ),
        (
            "Research future authentication/IDP options for post-MVP use",
            "pending", "research", None,
        ),
        (
            "Research HashiCorp Vault integration for deployment secrets after Compose secrets/env files are working",
            "pending", "research", None,
        ),
    ],
    "architecture-contracts": [
        (
            "Draft API route contract for project info, project sections/modules, project status, project tasks, agents, runs, and events",
            "completed", "planning",
            "Completed 2026-05-22 by Codex in docs/API-Contracts.md; keep it aligned with future OpenAPI/tests.",
        ),
        (
            "Draft database ERD or schema notes for projects, project_sections, status records, tasks, task events, agents, runs, leases, and reviews",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; docs/Architecture.md includes a Mermaid ERD and docs/Database.md holds schema planning notes.",
        ),
        (
            "Define nullable project_section_id behavior for project-wide/general status records and tasks",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; canonical behavior is null for project-wide/general work.",
        ),
        (
            "Define phase enum and validation behavior for status records and tasks",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; initial phases are planning, research, implementation, testing, and review.",
        ),
        (
            "Define optimistic locking/version fields for mutable resources",
            "completed", "planning",
            "Completed 2026-05-22 by Codex; docs/API-Contracts.md requires mutable resources to include version.",
        ),
        (
            "Establish standard API response formats for errors (422 Unprocessable Entity for validation) and collection pagination (page/per_page)",
            "completed", "planning",
            "Completed 2026-05-22 by Codex in docs/API-Contracts.md.",
        ),
        (
            "Evaluate pydantic-settings for type-safe configuration validation and failing fast on missing DATABASE_URL",
            "completed", "planning",
            "Completed 2026-05-22 by claude-sonnet-4-6; adopted in api/src/agent_workbench/config.py.",
        ),
        (
            "Define local/dev/stage/prod environment variable names in docs/Database.md",
            "completed", "planning",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Add example environment files for local, dev, stage, and prod without secrets",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; api/.env.example added.",
        ),
        (
            "Define idempotency key behavior for agent-submitted commands",
            "pending", "planning", None,
        ),
        (
            "Define task claim/lease/heartbeat behavior, including interaction with task assignee/owner",
            "pending", "planning", None,
        ),
        (
            "Define in-code API documentation strategy (e.g., OpenAPI auto-generation) to prevent API contract drift",
            "pending", "planning", None,
        ),
        (
            "Define append-only event model, structured logging fallback, and retention expectations",
            "pending", "planning", None,
        ),
        (
            "Define Markdown summary/mirroring strategy for MEMORY.md, TODO.md, and project status snapshots",
            "pending", "planning", None,
        ),
        (
            "Decide whether to split future contract details into generated OpenAPI plus this human-readable contract guide, or keep docs/API-Contracts.md as the canonical source through MVP",
            "pending", "planning", None,
        ),
    ],
    "scaffolding": [
        (
            "Establish api/, cli/, web/ top-level component directories with stubs for cli and web",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; cli/.gitkeep and web/.gitkeep added; Python API lives under api/.",
        ),
        (
            "Add backend project structure after framework decision",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; api/ directory with src/agent_workbench/, all 8 domain modules, blueprints, and SQLAlchemy models.",
        ),
        (
            "Add Docker Compose with local PostgreSQL 18 container and separate migrations service",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; docker-compose.yml with db, api (profile), and migrations (profile) services.",
        ),
        (
            "Add Docker Compose secret/env-file pattern for non-local deployment without committing secrets",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; env var pattern documented in api/.env.example and Makefile.",
        ),
        (
            "Add example env files without secrets",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; api/.env.example.",
        ),
        (
            "Add database migration tooling (Alembic) configured for semantic revision IDs and downgrade functions",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; api/alembic.ini, api/migrations/env.py, api/migrations/script.py.mako.",
        ),
        (
            "Add migration commands that require explicit APP_ENV for dev/stage/prod targets",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; make migrate-dev/stage/prod in Makefile require env vars and prod prompts for confirmation.",
        ),
        (
            "Add safe database bootstrap docs and SQL template for creating target schemas without embedding secrets",
            "completed", "implementation",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Expand root Makefile with setup, lint, test, smoke, integration-test, migration, cleanup, and real CLI build targets",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; full Makefile with API_DIR=api prefix for Python targets.",
        ),
        (
            "Add root Makefile with bootstrap task-next, status-show, validate, and placeholder build-cli targets",
            "completed", "implementation",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Configure pytest with autouse fixtures for per-test PostgreSQL 18 database cleanup",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; api/tests/conftest.py with session-scoped app/migration fixtures and autouse clean_db TRUNCATE; make test with --env-file .env.",
        ),
        (
            "Add curl smoke checks for API health and basic workflow validation",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; scripts/smoke-curl.sh covers health, projects, agents, events; make smoke target.",
        ),
        (
            "Add stub CLI/bootstrap commands for OpenCode: task next, claim, heartbeat, complete, block, status show",
            "completed", "implementation",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Confirm cli/builds/ is excluded from Git",
            "completed", "implementation",
            "Completed 2026-05-22 by Codex.",
        ),
        (
            "Scaffold Go CLI command tree using Cobra and Viper for config/env resolution",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; awb binary with task (next/list/get/claim/heartbeat/complete/block), project list, status show, version; builds to cli/builds/awb.",
        ),
        (
            "Add CLI install script and user-level config path support",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; scripts/install-awb.sh installs to ~/.local/bin or ~/bin; config resolves ~/.config/awb (preferred) then ~/.config/agent-workbench; yaml/json/toml all supported; make install-cli target added.",
        ),
        (
            "Add environment-aware wrapper command for running schema bootstrap against local/dev/stage/prod",
            "pending", "implementation", None,
        ),
        (
            "Add Python containerized integration-test runner",
            "pending", "implementation", None,
        ),
        (
            "Add post-MVP web scaffold using React + Express on Node.js 24 LTS with npm latest (only if MVP API/CLI queue is unblocked)",
            "pending", "implementation", None,
        ),
        (
            "Add scheduled OpenCode wrapper that calls bootstrap commands and runs one focused task",
            "pending", "implementation", None,
        ),
        (
            "Add optional Prometheus metrics dependencies and /metrics endpoint behind configuration",
            "pending", "implementation", None,
        ),
    ],
    "core-api-modules": [
        (
            "Implement projects module for project metadata, Git source location, type, environment, and defaults",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes (list, create, get, patch), service layer, serialization, optimistic locking, slug conflict handling.",
        ),
        (
            "Implement project_sections module for modules/sections within a project",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; nested CRUD routes under /api/projects/{id}/sections, sort_order support, project ownership validation.",
        ),
        (
            "Implement project_status module for project-wide and section-scoped current status and history",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; list/create/patch routes nested under /api/projects/{id}/status, optional project_section_id, optimistic locking.",
        ),
        (
            "Implement project_tasks module for project-wide and section-scoped tasks, priorities, phases, dependencies, assignee/owner, leases, and completion evidence",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; list/create at /api/projects/{id}/tasks; get/patch/claim/heartbeat/complete/block at /api/tasks/{id}/...; atomic lease via targeted UPDATE with rowcount check.",
        ),
        (
            "Implement agents module for agent registry, capabilities, defaults, and runtime hints",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; CRUD routes at /api/agents, name uniqueness enforced, optimistic locking.",
        ),
        (
            "Add per-task estimated_duration_seconds for local-AI-friendly lease windows",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; 3-level resolution (request > task estimate > 1800s default); 4 new tests.",
        ),
        (
            "Harden config: reject default SECRET_KEY in prod; add DB connectivity check to /health (503 on failure)",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
        (
            "Scaffold Go 1.26 CLI and configure builds to write artifacts into cli/builds/",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6.",
        ),
        (
            "Implement runs module for run attempts, heartbeats, validation, and outcomes",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; POST create, GET, heartbeat, complete, fail; atomic state transitions via targeted UPDATE.",
        ),
        (
            "Implement events module as append-only audit trail for status/task/run/review history",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; GET /api/projects/{id}/events and POST /api/events; no update/delete routes.",
        ),
        (
            "Implement reviews module for cloud review findings and signoff gates",
            "completed", "implementation",
            "Completed 2026-05-22 by claude-sonnet-4-6; list/create nested under project, PATCH /api/reviews/{id} for status updates.",
        ),
    ],
    "tests-quality": [
        (
            "Add API tests for all module contracts",
            "completed", "testing",
            "Completed 2026-05-22 by claude-sonnet-4-6; test_projects.py, test_tasks.py (incl. lease lifecycle + duration), test_agents.py, test_runs.py — 54+ tests passing.",
        ),
        ("Add unit tests for state transitions and validation", "pending", "testing", None),
        ("Add database integration tests using local PostgreSQL container", "pending", "testing", None),
        ("Add smoke script tests for health and minimal task lifecycle", "pending", "testing", None),
        (
            "Add Python containerized integration tests for multi-project workflows and task leases",
            "pending", "testing", None,
        ),
        ("Run lint, format check, type check, build, and tests when available", "pending", "testing", None),
        ("Review with QUALITY_CHECKLIST.md", "pending", "review", None),
    ],
    "docs-deployment": [
        (
            "Add database environment and schema planning doc",
            "completed", "review",
            "Completed 2026-05-22 by Codex in docs/Database.md.",
        ),
        (
            "Document bootstrap CLI command workflow for OpenCode in docs/Bootstrap-CLI.md",
            "completed", "review",
            "Completed 2026-05-22 by Codex.",
        ),
        ("Update README.md with setup and bootstrap workflow", "pending", "review", None),
        ("Add docs/Development.md after Compose/scripts exist", "pending", "review", None),
        ("Document deployment, environment variables, and operational notes", "pending", "review", None),
        ("Document database migration workflow", "pending", "review", None),
        (
            "Document secret handling, Docker Compose secrets/env files, Vault future option, and Ansible integration expectations without copying secrets",
            "pending", "review", None,
        ),
        (
            "Document OpenCode automation workflow once the OpenCode setup repo is ready",
            "pending", "review", None,
        ),
        (
            "Document post-MVP web UI scope for human review and adding tasks on the fly, using React + Express on Node.js 24 LTS",
            "pending", "review", None,
        ),
        ("Document optional Prometheus setup and scrape example", "pending", "review", None),
        ("Record decisions and milestones in MEMORY.md", "pending", "review", None),
    ],
}

# ── Seed logic ────────────────────────────────────────────────────────────────


def seed() -> None:
    app = create_app()
    with app.app_context():
        # Project
        existing = db.session.scalar(select(Project).where(Project.slug == PROJECT_DATA["slug"]))
        if existing:
            print(f"Project '{PROJECT_DATA['slug']}' already exists — skipping project creation.")
            project = existing
        else:
            project = projects_service.create_project(PROJECT_DATA)
            print(f"Created project: {project.name} ({project.id})")

        # Sections
        section_map: dict[str, ProjectSection] = {}
        for sec_data in SECTIONS:
            existing_sec = db.session.scalar(
                select(ProjectSection).where(
                    ProjectSection.project_id == project.id,
                    ProjectSection.slug == sec_data["slug"],
                )
            )
            if existing_sec:
                print(f"  Section '{sec_data['slug']}' already exists — skipping.")
                section_map[sec_data["slug"]] = existing_sec
            else:
                sec = sections_service.create_section(project.id, sec_data)
                section_map[sec_data["slug"]] = sec
                print(f"  Created section: {sec.name}")

        # Tasks
        total_created = 0
        total_skipped = 0
        for section_slug, task_list in TASKS.items():
            section = section_map.get(section_slug)
            if section is None:
                print(f"  WARNING: section '{section_slug}' not found — skipping its tasks.")
                continue
            for title, status, phase, evidence in task_list:
                existing_task = db.session.scalar(
                    select(Task).where(
                        Task.project_id == project.id,
                        Task.project_section_id == section.id,
                        Task.title == title,
                    )
                )
                if existing_task:
                    total_skipped += 1
                    continue
                task_data: dict = {
                    "title": title,
                    "status": status,
                    "phase": phase,
                    "project_section_id": str(section.id),
                }
                if evidence:
                    task_data["completion_evidence"] = evidence
                tasks_service.create_task(project.id, task_data)
                total_created += 1

        db.session.commit()
        print(
            f"\nDone. Created {total_created} tasks, skipped {total_skipped} existing. "
            f"Project ID: {project.id}"
        )


if __name__ == "__main__":
    seed()
