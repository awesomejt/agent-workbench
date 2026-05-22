# Quality Checklist

Use this before asking for final review, opening a pull request, or releasing.

## Requirements

- [ ] `PROJECT_BRIEF.md` is complete enough for implementation.
- [ ] `docs/Requirements.md` describes user-visible behavior and success criteria.
- [ ] Open questions are recorded in `MEMORY.md` or `TODO.md`.
- [ ] Out-of-scope items are not accidentally implemented.

## Code Quality

- [ ] Code follows the selected stack and local conventions.
- [ ] Changes are focused and reviewable.
- [ ] Public interfaces, schemas, routes, commands, or configs are documented.
- [ ] Error states and empty states are handled where relevant.
- [ ] Secrets and credentials are not committed.

## Tests And Validation

- [ ] Unit tests cover important logic.
- [ ] Integration or end-to-end tests cover critical workflows when appropriate.
- [ ] Lint, format check, type check, build, and test commands pass when available.
- [ ] Manual validation tasks are listed in `TODO.md`.

## Frontend Or UX

- [ ] Main workflows are easy to complete.
- [ ] Text fits in the UI at supported screen sizes.
- [ ] Loading, empty, disabled, and error states are clear.
- [ ] Accessibility basics are addressed.

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
