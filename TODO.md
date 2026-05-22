# Project TODO

Task list for `{{PROJECT_NAME}}`, organized by ownership and project phase.

## Needs Attention

Items here require Jason's input, a decision, credentials, external access, or manual validation before agent work can continue.

- [ ] Replace all `{{PLACEHOLDER}}` values in project files before starting agent work.

## Manual Validation

These items need Jason to validate on real systems, live services, devices, accounts, or deployment targets.

- [ ] Confirm requirements and success criteria in `PROJECT_BRIEF.md`.
- [ ] Confirm chosen stack and deployment target.
- [ ] Confirm credentials, API keys, and production access are not committed.
- [ ] Validate deployment or release workflow on the target environment.

## AI Agent Work

These items are good candidates for a local model or cloud agent.

### Discovery

- [ ] Read `PROJECT_BRIEF.md`, `MEMORY.md`, `TODO.md`, `status.yaml`, and relevant docs.
- [ ] Inventory existing source, tests, configs, and docs.
- [ ] Identify missing requirements and blockers.

### Planning

- [ ] Fill in `docs/Requirements.md`.
- [ ] Fill in `docs/Tech-Stack.md`.
- [ ] Fill in or intentionally skip `docs/Architecture.md`.
- [ ] Update `docs/Implementation.md` with implementation phases.

### Implementation

- [ ] Scaffold the chosen project structure.
- [ ] Implement the highest-priority unblocked feature or fix.
- [ ] Update public interfaces, schemas, or configuration docs as needed.

### Tests And Quality

- [ ] Add or update unit tests.
- [ ] Add or update integration/e2e tests where risk justifies it.
- [ ] Run lint, format check, type check, build, and test commands when available.
- [ ] Review with `QUALITY_CHECKLIST.md`.

### Documentation And Deployment

- [ ] Update `README.md` setup and usage instructions.
- [ ] Document deployment, environment variables, and operational notes.
- [ ] Record decisions and milestones in `MEMORY.md`.

## In Progress

Move exactly one task here while working if multiple agents may run at the same time.

- [ ]

## Blocked

Move blocked tasks here with the blocker and the next required human action.

- [ ]

## Done

Move completed items here with a brief note.

- [ ]
