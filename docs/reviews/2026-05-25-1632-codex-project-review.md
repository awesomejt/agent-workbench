# Codex Project Review - 2026-05-25 16:32

Reviewer: Codex

Scope: project contracts, API implementation, CLI, smoke/integration tooling, web build stub, deployment/development docs.

Task source: `awb task list --available` for `agent-workbench` returned no available tasks, so this review was performed from Jason's direct request and recorded here.

## Executive Summary

The API core is in better shape than the surrounding dogfood tooling: Python validation, mypy, the PostgreSQL-backed pytest suite, CLI build/vet, clean-clone CLI build, and web build all pass. The main risks are contract drift and agent workflow reliability: the documented `--project` CLI flag does not satisfy project-scoped commands, the smoke target hides a failing smoke script, direct task claims can bypass `blocks` dependencies, and phase/project-type invariants can drift into invalid database state.

## Findings

### P0 - `awb --project ...` does not populate project-scoped commands

The documented CLI examples rely on `--project`, but project-scoped commands still fail with `--project is required` when the flag is passed:

```bash
./cli/builds/awb --project agent-workbench task list --available
./cli/builds/awb task list --available --project agent-workbench
```

Both failed before contacting the API. The equivalent environment-variable form proceeds to the API:

```bash
AWB_PROJECT=agent-workbench ./cli/builds/awb task list --available
```

Relevant code:

- `cli/cmd/root.go:38` defines the `--project` persistent flag.
- `cli/cmd/root.go:43` binds persistent flags into Viper.
- `cli/cmd/root.go:63` reads required values through `viper.GetString`.
- `cli/cmd/task.go:20` and `cli/cmd/task.go:95` require `project` for task list/next.
- `scripts/opencode-run.sh:88` uses the broken `--project` flag in its API preflight.
- README and development docs advertise the broken form in `README.md:37` and `docs/Development.md:246`.

Impact: the documented dogfood workflow and `opencode-run.sh` preflight can fail even when the API is healthy. Agents can work around it with `AWB_PROJECT`, but the flag path needs a regression test and a fix.

### P0 - `make smoke` reports success even when smoke checks fail

`scripts/smoke-curl.sh` currently creates a project with `project_type:"generic"` at `scripts/smoke-curl.sh:64`, but the API only accepts `code`, `course`, `content`, `research`, `infrastructure`, or `other` in `api/src/agent_workbench/projects/routes.py:13`. Running `make smoke` produced:

```text
FAIL  [got 422, want 201] POST /api/projects creates project
Results: 5 passed, 1 failed
smoke-curl.sh not yet implemented
```

Despite that failure, `make smoke` exited successfully because the Makefile swallows any script failure at `Makefile:166`.

Impact: the smoke gate can look green while skipping the task lifecycle checks that depend on project creation. Change the smoke fixture to a valid project type and make the target fail when the script fails.

### P1 - Direct task claims can bypass incomplete `blocks` relationships

The available-task query correctly filters out tasks blocked by incomplete predecessors in `api/src/agent_workbench/tasks/service.py:55`, and the relationship tests cover that list behavior in `api/tests/test_task_relationships.py:187`. The claim path, however, only checks task status and lease expiry in `api/src/agent_workbench/tasks/service.py:133` and `api/src/agent_workbench/tasks/routes.py:286`.

Impact: any caller with a task ID can `POST /api/tasks/{id}/claim` and start a task whose `blocks` predecessor is still incomplete. That undermines the coordination guarantee once agents retry stale IDs or work from copied task links. The claim transaction should enforce the same unblocked predicate as `available=true`, with a direct regression test.

### P1 - Project phase can move backward despite the high-water contract

`docs/State-Machines.md:103` says project phase is forward-only and never moves backward. Implementation reads the current phase from the most recent status row in `api/src/agent_workbench/project_status/service.py:54`, while manual create/patch accepts any valid phase in `api/src/agent_workbench/project_status/routes.py:70` and `api/src/agent_workbench/project_status/routes.py:93`.

Impact: a manual `design` status after a `review` status makes the project look like it moved backward. Later auto-advance uses that newest lower phase as the baseline. Either reject lower manual phases, compute current phase as the max ordinal, or document an explicit override model.

### P1 - New projects default to an invalid `project_type`

The route validator allows only the canonical project types at `api/src/agent_workbench/projects/routes.py:13`, and the model default is `code` at `api/src/agent_workbench/projects/models.py:22`. The service overrides both by defaulting omitted `project_type` to `development` in `api/src/agent_workbench/projects/service.py:29`.

Impact: projects created without an explicit type contain a value that could not be submitted explicitly and is outside the documented project vocabulary. Change the service default to `code` and add a default-value test.

### P2 - Section slugs are not actually unique per project

`create_section` catches `IntegrityError` and reports "A section with slug ... already exists in this project" at `api/src/agent_workbench/project_sections/routes.py:79`, but `ProjectSection.slug` is only indexed in `api/src/agent_workbench/project_sections/models.py:31`. There is no unique constraint on `(project_id, slug)`.

Impact: duplicate section slugs can be created, making future CLI/web selection by slug ambiguous. Add a unique constraint and migration, then add a duplicate-section test.

### P2 - Review `linked_task_id` accepts dangling or cross-project links

Review create/update validates only UUID syntax for `linked_task_id` in `api/src/agent_workbench/reviews/routes.py:88` and `api/src/agent_workbench/reviews/routes.py:127`. The service writes that ID directly in `api/src/agent_workbench/reviews/service.py:37` and `api/src/agent_workbench/reviews/service.py:49`.

Impact: a nonexistent task ID will fall through to a database foreign-key error instead of a structured 422, and a task from another project can be linked to the review. Validate existence and project ownership before committing.

### P2 - Contract docs have drifted from implemented routes and workflow rules

Several docs no longer match the code or the current dogfood policy:

- `docs/API-Contracts.md:175` omits implemented task fields such as `role`, `model_tier`, and `estimated_duration_seconds`, plus the relationship routes in `api/src/agent_workbench/tasks/routes.py:460`.
- `docs/API-Contracts.md` does not document the implemented `/api/ai-servers` module from `api/src/agent_workbench/ai_servers/routes.py:18`.
- `docs/API-Contracts.md:320` lists review statuses as `draft`, `published`, `accepted`, `rejected`, while the implementation accepts `open`, `resolved`, `deferred` in `api/src/agent_workbench/reviews/routes.py:15`.
- `docs/Development.md:261` and `docs/Bootstrap-CLI.md:70` still tell agents to update `TODO.md`, contradicting `AGENTS.md` and `MEMORY.md`, which say the workbench API is authoritative and `TODO.md` is read-only.
- `docs/Deployment.md:124` shows `agent_workbench` and `agent_workbench_prod` in the production URL, conflicting with the same document's `awb` user and `agent_workbench` database policy at `docs/Deployment.md:42`.

Impact: agents following the docs can use stale statuses, stale CLI behavior, or the wrong deployment values. Do a contract-doc cleanup after the P0/P1 behavior fixes.

## Positive Notes

- `make validate` passes with imports, ruff, format check, and mypy.
- `make test` passes 211 PostgreSQL-backed tests.
- Atomic task claims, lease expiry, idempotency, run events, and most state-machine guards have good focused tests.
- `make cli-vet`, `make build-cli`, `make cli-test`, and `make cli-clean-build-check` pass, though the CLI has no Go test files yet.
- `npm run build` succeeds for the current web stub.

## Validation Run

- `git pull --ff-only`: already up to date.
- `AWB_PROJECT=agent-workbench AWB_AGENT=codex-review AWB_API_URL=http://localhost:8000 ./cli/builds/awb task list --available`: no tasks found.
- `make validate`: passed.
- `make test`: 211 passed.
- `make cli-vet`: passed.
- `make build-cli`: passed.
- `make cli-test`: passed, but all packages reported no test files.
- `make cli-clean-build-check`: passed.
- `npm run build` in `web/`: passed.
- `make smoke`: script reported 1 failing check, but the Makefile target exited successfully.

Not run: `make integration-test` containerized suite. The API-level pytest suite and smoke check were run instead.

## Recommended Fix Order

1. Fix CLI `--project` handling and add CLI tests for persistent flags.
2. Fix `scripts/smoke-curl.sh` and make `make smoke` fail on smoke failures.
3. Enforce `blocks` dependencies inside the claim path.
4. Fix project phase high-water behavior and project-type defaults.
5. Add section uniqueness and review linked-task ownership validation.
6. Sweep contract docs after the behavior fixes land.
