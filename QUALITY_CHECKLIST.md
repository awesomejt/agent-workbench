# Quality Checklist

Use this before asking for final review, opening a pull request, or releasing.

## Requirements

- [ ] `PROJECT_BRIEF.md` is complete enough for implementation.
- [ ] `docs/Requirements.md` describes user-visible behavior and success criteria.
- [ ] Open questions are recorded in `MEMORY.md` or `TODO.md`.
- [ ] Out-of-scope items are not accidentally implemented.

## Contract Alignment

- [ ] API routes, request/response fields, errors, and state transitions match docs and tests.
- [ ] Scripts/CLI commands match the documented agent workflow.
- [ ] Database schema and migrations match the documented data model.
- [ ] Docker/Compose services and environment variables match setup docs.
- [ ] Generated or migrated code does not leave stale names, old endpoint paths, or imagined fields behind.

## Code Quality

- [ ] Code follows the selected stack and local conventions.
- [ ] Changes are focused and reviewable.
- [ ] Public interfaces, schemas, routes, commands, or configs are documented.
- [ ] Error states and empty states are handled where relevant.
- [ ] Secrets and credentials are not committed.

## Tests And Validation

- [ ] Unit tests cover important logic and state transitions.
- [ ] Integration or end-to-end tests cover critical workflows when appropriate.
- [ ] Lint, format check, type check, build, and test commands pass when available.
- [ ] Smoke or integration checks validate cross-module behavior when API, scripts/CLI, or Docker contracts change.
- [ ] Test fixtures match the real application factory, database backend, route paths, and response shapes.
- [ ] Manual validation tasks are listed in `TODO.md`.

## Operations

- [ ] Setup instructions are current.
- [ ] Environment variables are documented without exposing secret values.
- [ ] Deployment or release steps are documented.
- [ ] Rollback or recovery notes exist when the project needs them.

## Agent Handoff

- [ ] `MEMORY.md` contains current status, decisions, blockers, and next recommended task.
- [ ] `TODO.md` has active tasks in the correct lanes.
- [ ] Done items are moved to Done.
- [ ] Manual validation tasks are not hidden inside AI task lists.
- [ ] Any commits are small, logical, and clearly named.

## Cloud Review

- [ ] A cloud-based AI review has checked contract alignment across API, database, scripts/CLI, Docker, docs, and tests before real use.
- [ ] Review findings are captured in `TODO.md` with severity or risk ordering.
- [ ] Refactors from review are split into focused tasks with validation.
- [ ] Production-readiness risks, test gaps, and deployment assumptions are documented.
