# Agent Workbench Repo And CLI Recommendations

## Objective

Review the full repository with extra attention on the Go CLI client, then leave actionable recommendations for Claude to review.

Important fixed constraint from Jason: keep Flask for the API. These recommendations assume Flask remains the API framework.

## Scope Reviewed

- Root project contract files: `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, `status.yaml`, `AGENT_WORKFLOW.md`, `QUALITY_CHECKLIST.md`, `README.md`
- Docs: `docs/Requirements.md`, `docs/Tech-Stack.md`, `docs/Architecture.md`, `docs/Implementation.md`, `docs/API-Contracts.md`, `docs/Bootstrap-CLI.md`, `docs/Database.md`
- Go CLI: `cli/cmd/*`, `cli/internal/api/*`, `cli/internal/output/output.go`, `cli/go.mod`
- Bootstrap scripts: `scripts/awb.py`, task wrapper scripts, `scripts/install-awb.sh`, `scripts/smoke-curl.sh`
- Flask API routes/services/models/tests across `api/src/agent_workbench` and `api/tests`
- Config and local deployment files: `Makefile`, `docker-compose.yml`, `.gitignore`, env examples

## Validation Run

- `git pull --ff-only`: already up to date.
- `cd cli && go test ./...`: passes locally, but only because ignored local files are present.
- `cd cli && go vet ./...`: passes locally.
- Clean Git archive CLI test: fails because `cli/internal/output/output.go` is ignored and absent from the archive.
- `cd api && UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src tests`: passes.
- `cd api && UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check src tests`: fails; 15 files would be reformatted.
- `cd api && UV_CACHE_DIR=/tmp/uv-cache uv run mypy src`: fails with 17 errors.
- `cd api && UV_CACHE_DIR=/tmp/uv-cache uv run --env-file .env pytest`: passes with escalated localhost DB access; 54 passed in 0.86s.

Note: pytest failed inside the default sandbox because it could not connect to the local PostgreSQL container on `localhost:5433`. Re-running with local DB access passed.

## Highest Priority Recommendations

### 1. Fix the ignored CLI output package before anything else

Risk: clean clones and CI can fail even though Jason's current working tree builds.

Evidence:

- `cli/cmd/*.go` imports `agent-workbench/cli/internal/output`.
- `cli/internal/output/output.go` exists locally.
- `.gitignore` has a broad `output/` rule that ignores any directory named `output`, including `cli/internal/output/`.
- `git check-ignore -v cli/internal/output/output.go` reports `.gitignore:40:output/`.
- A clean Git archive of `HEAD` fails with `package agent-workbench/cli/internal/output is not in std`.

Recommended fixes:

- Best: rename the package directory from `cli/internal/output` to something not globally ignored, such as `cli/internal/render` or `cli/internal/format`.
- Acceptable: add explicit negation rules after `output/`, for example `!cli/internal/output/` and `!cli/internal/output/*.go`.
- Add a clean-check validation command so this cannot recur.

### 2. Add CLI tests and clean-clone build validation

Risk: the CLI has no test files, so `go test ./...` mostly verifies compilation against whatever happens to exist locally.

Recommended coverage:

- `internal/api`: use `httptest.Server` to verify paths, methods, JSON bodies, query parameters, errors, and timeout behavior.
- `cmd`: command tests for `--project`, `--agent`, `--output json`, missing required flags, and table output.
- Config: test Viper precedence: flag > env > config file > default.
- Clean clone: add a Make target or CI check that builds from tracked files only, or at least assert `git ls-files cli/internal/...` includes required source.

Suggested Make targets:

- `cli-test`: `cd cli && go test ./...`
- `cli-clean-build-check`: build from a `git archive` temp copy.

### 3. Make `awb task next` agent-safe

Risk: `awb task next` can currently show a pending task that is already leased by another agent.

Current behavior:

- `awb task next` calls `GET /api/projects/{project_id}/tasks?status=pending&per_page=1`.
- The API `status=pending` filter does not exclude rows with `claimed_by` and an unexpired `claimed_until`.
- The later claim request will conflict, but the "next" command is supposed to guide agents toward useful work.

Recommended API/CLI shape:

- Add an API filter such as `available=true` that means pending and either unclaimed or lease expired.
- Better for agents: add a single atomic "claim next" route or CLI command so discover-and-claim is one transaction.
- Add CLI flags: `awb task next --available`, `awb task list --available`, `--assignee`, `--phase`, `--limit`.
- Add tests with claimed/unclaimed/expired-leased tasks.

### 4. Finish event creation for state transitions

Risk: docs say task claims, heartbeats, completions, blocks, status changes, run transitions, and review transitions append durable events, but the implementation mostly changes rows without appending events.

Current state:

- `/api/events` can append explicit events.
- Task lifecycle service methods do not append events automatically.
- Run transitions do not append events automatically.
- Status/review/project changes do not append events automatically.

Recommended fix:

- Add a small Flask-compatible event helper/service used inside the same DB transaction as the state change.
- Include event payloads with before/after status, actor, task/run/review ID, idempotency key when present, and validation evidence summary.
- Add tests that each transition both changes state and appends the expected event.

### 5. Define and implement idempotency behavior for CLI transitions

Risk: retrying agent commands can still produce conflicts or ambiguous results.

Current state:

- API accepts `idempotency_key` on task claim only.
- CLI does not send idempotency keys.
- `tasks.idempotency_key` is globally unique on the task row, which is not enough to model retry-safe transitions over time.

Recommended fix:

- Decide the idempotency scope: endpoint + actor + key is usually safer than a single task column.
- Add CLI support: `--idempotency-key`, plus optional auto-generation from task ID, agent name, command, and run ID.
- Store idempotency records or events with request hash and response summary.
- Replays with the same key and same request should return the original result; same key with different body should return `409`.

### 6. Expand the CLI to cover the MVP API surface, but in a staged order

Current CLI covers:

- `project list`
- `status show`
- `task list/get/next/claim/heartbeat/complete/block`
- `version`

Important missing surfaces:

- `agent list/create/get/update`
- `run start/get/heartbeat/complete/fail`
- `event list/append`
- `review list/create/update`
- `project create/get/update`
- `section list/create/get/update`
- `status create/update`

Recommended order:

1. Fix build tracking and add tests.
2. Harden task workflow commands because agents depend on them first.
3. Add run commands so every agent session can create a durable run and heartbeat.
4. Add event list/append for debugging and audit trails.
5. Add agent and project CRUD commands for Jason/admin workflows.
6. Add reviews after cloud review workflow stabilizes.

### 7. Improve CLI ergonomics and failure modes for agents

Recommended changes:

- Validate `--output` and fail early for unsupported values.
- Avoid double-printing errors. `output.Err` writes to stderr and returns an error; Cobra/root also prints the returned error.
- Avoid nil/panic edges: `taskClaimCmd` dereferences `*task.ClaimedBy`; task list slices `t.ID[:8]`.
- Trim trailing slashes from `--api-url` to avoid malformed URLs like `http://x//api/...`.
- Add timeout config: `--timeout`, `AWB_TIMEOUT`, config file value.
- Add retry policy only for safe requests or idempotency-protected transitions.
- Add `--page` and `--per-page` flags instead of hard-coding 50 or 100.
- Prefer `GET /api/projects?slug=...` or a `GET /api/projects/by-slug/{slug}` route instead of resolving a slug by listing the first 100 projects.
- Add shell completion as the next planned CLI polish task after correctness fixes.

### 8. Tighten API validation and relationship checks

These are Flask-compatible service/route improvements, not framework changes.

Recommended checks:

- Validate `duration_seconds` is an integer within a reasonable positive range; invalid values currently can raise unhandled conversion errors.
- Validate task/status `project_section_id` exists and belongs to the same project.
- Validate `task_id` on run creation exists and belongs to the provided project.
- Validate event foreign key references, or catch `IntegrityError` and return structured `409`/`422` instead of an internal error.
- Add enum validation for task status, run status, review status/severity, project status, phase, assignee type, and environment.
- Decide whether block should clear the lease like complete does, or keep the lease intentionally; document and test either way.

### 9. Align docs with current behavior

Recommended doc cleanup:

- `docs/Bootstrap-CLI.md` says Phase 2 exit criteria include transition events; implementation does not yet append them automatically.
- `docs/Requirements.md` lists runtime metrics fields on runs, but the `runs` table does not have them yet and TODO still tracks that work. Mark clearly as planned.
- Root `.env.example.local` uses port 5432 and password `agent_workbench_dev`, while `api/.env.example` and Compose use port 5433 and password `agent_workbench_local`. Align the root example.
- `README.md` current status still says planning/bootstrap; repo is now in implementation with a functional API and partial CLI.
- If `cli/internal/output` is renamed, update all docs that mention command output expectations only if behavior changes.

### 10. Bring formatting and type-checking into the actual quality gate

Current validation signal:

- Ruff lint passes.
- Ruff format check fails on 15 files.
- Mypy fails with 17 issues, mostly Flask-SQLAlchemy typing, rowcount typing, and required `Settings.database_url`.
- Pytest passes when local PostgreSQL is reachable.

Recommended approach:

- Run `ruff format` in a focused formatting-only commit.
- Either configure mypy for Flask-SQLAlchemy patterns or add targeted typing adjustments.
- Make `make validate` include CLI tests/build and Python checks once the current failures are resolved.
- Consider separate targets: `validate-fast`, `validate-db`, and `validate-clean-clone`.

## Medium Priority Recommendations

### Add a generated or executable API contract strategy

The hand-authored API contract is useful, but drift risk is rising now that the Flask app exists.

Options that preserve Flask:

- Add `flask-smorest` or another Flask-friendly OpenAPI tool later.
- Generate a lightweight route map from Flask and compare it against `docs/API-Contracts.md`.
- Add contract tests for every route in `docs/API-Contracts.md`, especially modules not currently covered by tests.

### Improve bootstrap script transition plan

The Python bootstrap scripts still operate from Markdown/local state. That is okay as fallback, but the repo should make the transition explicit:

- Either keep scripts as Phase 1 fallback only.
- Or make scripts delegate to `awb` when `AWB_API_URL` or config is present, falling back to Markdown state only when API is unavailable.
- Preserve output shapes used by OpenCode scheduled runs.

### Add local development safeguards

Recommended:

- `make test` should check that local PostgreSQL is reachable and print a friendly hint if not.
- Provide a `make test-db-up` or `make db-test-setup` target for creating `agent_workbench_test`.
- Document that sandboxed agents may need elevated localhost access to run DB-backed pytest.

## Suggested Claude Task Order

1. Fix `cli/internal/output` being ignored and prove a clean Git archive can build.
2. Add CLI tests for current commands and API client behavior.
3. Make task next/list availability lease-aware, with tests.
4. Add automatic event appends for task transitions, with tests.
5. Add CLI idempotency keys for claim/heartbeat/complete/block after API semantics are defined.
6. Format the Python codebase and decide how strict mypy should be for this MVP.
7. Add run commands to the CLI so real agent sessions can be tracked end-to-end.
8. Align docs/env examples with actual current behavior.

## Notes For Claude

- Do not suggest replacing Flask; Jason explicitly wants to keep Flask.
- Prefer small, vertical fixes that keep API, CLI, tests, docs, and Makefile aligned.
- The highest-risk issue is the ignored Go package because it can fool local validation.
- The highest product-risk issue is task selection/claiming not being truly agent-safe yet.
- The highest contract-drift issue is documented event/idempotency behavior not matching implementation.
