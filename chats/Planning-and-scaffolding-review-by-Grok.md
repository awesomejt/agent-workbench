## Prompt

Access my agent-workbench project on GitHub. Review the work done so far, make recommendations on improvement. There is some existing code, but the focus should be on the documentation, direction, guidelines for agentic workflow, and scaffolding done so far. Existing code in the cli will be refactored based on a MVP-driven approach with a working api and cli with a web ui added later.

## Response

**The `agent-workbench` repo is in a strong early bootstrap/planning phase.** It shows thoughtful, agent-aware design with heavy emphasis on documentation, clear separation of concerns, and a pragmatic MVP path (API + CLI first, web UI later). This aligns well with your stated focus: refactor existing CLI code via an MVP-driven approach.

### Overall Strengths
- **Documentation excellence**: Comprehensive root files (`PROJECT_BRIEF.md`, `README.md`, `AGENT_WORKFLOW.md`, `AGENTS.md`, `MEMORY.md`, `TODO.md`, `QUALITY_CHECKLIST.md`) plus dedicated `docs/` coverage (Architecture, Requirements, Database, Implementation, Tech-Stack, Bootstrap-CLI, etc.). This creates a robust knowledge base for agents and humans, minimizing context loss.
- **Clear direction**: Modular monolith with PostgreSQL as the long-term source of truth, Git for code, Markdown as a temporary bridge. Strong emphasis on agent safety (leases, heartbeats, idempotency, events, optimistic locking).
- **MVP alignment**: Prioritizes API (Python/Flask) + CLI/scripts (Go/Cobra or Python stubs) over premature web UI. Bootstrap scripts in `scripts/` provide immediate value for OpenCode/local loops.
- **Agent-centric design**: Workflows account for context resets, contract alignment, cloud review gates, and blocker handling. This is sophisticated for an early-stage project.
- **Scaffolding**: Env examples, .gitignore, Makefile, status.yaml, and stub commands show solid foundations. Database planning (local container → env-driven dev/stage/prod) is mature.

### Areas for Improvement & Recommendations

#### 1. Documentation (Strong but Can Be Polished)
**Strengths**: Thorough and living. Root files + `docs/` reduce drift.

**Recommendations**:
- **Centralize contracts**: Create `docs/API-Contracts.md` (or expand Architecture) with OpenAPI-style summaries for routes, request/response shapes, error formats, and state machines. Reference it everywhere to enforce alignment.
- **Visual aids**: Add simple diagrams in `docs/diagrams/` (e.g., ERD for projects/tasks/runs/events, agent workflow sequence, module boundaries). Use tools like Mermaid or PlantUML for maintainability.
- **Versioning/Change log**: Add a lightweight `CHANGELOG.md` or section in MEMORY.md for high-level decisions. Link TODO items to specific decisions.
- **Bootstrap transition plan**: Expand `docs/Bootstrap-CLI.md` with a phased roadmap: (1) Markdown + stubs, (2) API-backed CLI, (3) Full DB coordination + mirroring to Markdown.
- **Keep concise**: Aim for scannable Markdown (tables, checklists). Agents love brevity.

#### 2. Project Direction & Priorities
**Current state**: Planning/bootstrap heavy; TODO.md is well-organized with lanes (Needs Attention, Review, Discovery, etc.).

**Recommendations** (MVP-driven):
- **Prioritize core data model**: Finish database schema/ERD (projects, sections, status, tasks with leases/assignee/owner/phase, runs, events). This unblocks everything. Use Alembic for migrations early.
- **API-first scaffolding**: Define routes (e.g., `/api/projects`, `/api/projects/{id}/tasks`, `/api/tasks/claim`, heartbeats) and implement minimal Flask app with Pydantic for validation/config. Include health checks and basic CRUD.
- **CLI as thin client**: Build Go CLI (or Python) to call the API for agent workflows. Refactor existing `scripts/` (which are good stubs) into this. Makefile targets for `build-cli`, `run-api`, etc.
- **Task lifecycle rigor**: Ensure atomic claims, expiration on leases, heartbeats, and append-only events are in the first data model.
- **Defer non-MVP**: Web UI (React), auth/IDP, Vault, K3s, full Prometheus — all post-MVP as planned. Focus on Docker Compose + local Postgres for immediate usability.
- **Discovery & mirroring**: Early feature to scan `~/projects/*` Git repos and mirror summaries back to TODO/MEMORY.

**Risks to watch**:
- Contract drift (docs vs. code vs. scripts). Enforce via `QUALITY_CHECKLIST.md` and cloud review gates.
- Over-documenting early: Balance with working code.

#### 3. Guidelines for Agentic Workflow
**AGENT_WORKFLOW.md** and **AGENTS.md** are excellent.

**Recommendations**:
- **Refine task selection**: Explicitly weight by impact (e.g., unblocking architecture > features).
- **Validation emphasis**: Mandate "relevant validation" (smoke, tests, contract checks) before Done. Add Makefile targets like `make validate`, `make test-integration`.
- **Cloud review process**: Formalize as a recurring TODO item or script-triggered review. Include checklist for data integrity, error handling, and lease safety.
- **State management**: Clarify transitions in a diagram/table. Agents should always restore `status.yaml` properly.
- **Chat/transcript handling**: Good `chats/` practice; consider auto-mirroring via workflow manager.
- **Multi-agent safety**: Strong emphasis on leases/heartbeats — double down here for concurrent runs.

Update workflows to reference the future API/CLI more explicitly as it matures.

#### 4. Scaffolding & Existing Code (CLI-Focused Refactor)
**Current**: Good stubs (`scripts/` + `awb.py`), env examples, Makefile, Docker-ready thinking. No heavy code yet (ideal for MVP).

**Recommendations**:
- **Refactor path**: Treat `scripts/` as prototypes. Migrate logic to a proper CLI (Go preferred for static binaries) or Python CLI that talks to the Flask API. Keep scripts as thin wrappers during transition.
- **Structure**:
  - `backend/` or `api/` for Flask app (with `app/`, `models/`, `routes/`, `schemas/`, `migrations/`).
  - `cli/` for Go source + builds (ignored).
  - `docs/`, `scripts/` (transitional), `tests/`.
- **Dev experience**: Add `docker-compose.yml` (Postgres + API service) ASAP. Env file handling, `make up`, `make migrate`, `make test`.
- **Testing**: Pytest with test DB fixtures. Start with contract/smoke tests.
- **Python stack**: Confirm uv + Python 3.14, Flask, SQLAlchemy/Alembic, Pydantic. Add dependencies gradually.
- **Security/ops**: Never commit secrets (good .gitignore). Document env vars thoroughly in `docs/Database.md` and examples.

**Immediate next steps** (from TODO alignment):
1. Finalize data model + API contracts.
2. Scaffold Flask app + Alembic.
3. Docker Compose.
4. Go CLI skeleton + refactor stubs.
5. Cloud review gate before deeper implementation.

### Summary
This is a **high-quality foundation** for an agent coordination platform. The documentation and agent guidelines are standout features that will pay dividends as the system scales. Focus remains sharp on MVP (working API + refactored CLI for task coordination), which positions you well for rapid progress with local agents/OpenCode.

The project is documentation-heavy by design (smart for context resets), but shifting to working code in the next phase will make it even more compelling. Prioritize the database schema and basic API/CLI loop to enable real agent usage quickly. 

If you'd like me to dive deeper (e.g., propose specific schema, API routes, Makefile expansions, or even draft files), provide feedback on any doc, or help with scaffolding code, just let me know!