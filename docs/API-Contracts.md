# API Contracts

Canonical planning contract for the Agent Workbench API/CLI MVP. Keep this file aligned with `docs/Requirements.md`, `docs/Architecture.md`, `docs/Database.md`, `docs/Implementation.md`, `TODO.md`, future OpenAPI output, tests, and CLI command docs.

This is intentionally OpenAPI-style without becoming a full generated spec yet. Once the Flask app exists, either generate OpenAPI from code or make this document the source used to create tests and examples.

## Contract Principles

- Canonical routes are multi-project aware.
- API routes are not URL-versioned for MVP; compatibility and deprecation notes must be documented when routes change.
- State-changing agent actions use explicit transition routes when atomic behavior matters.
- Mutable resources include optimistic version fields.
- Retryable agent actions accept idempotency keys.
- Task claims, heartbeats, completions, blocks, and review transitions append durable events.
- CLI/scripts are thin clients over the same API contract once bootstrap state is replaced.

## Shared Types

### Identifiers

- IDs are UUID strings.
- `project_section_id` may be `null` for project-wide/general work.

### Phases

Initial phase values:

- `discovery`
- `design`
- `implementation`
- `testing`
- `review`

### Assignment

Tasks should identify the responsible party without assuming every worker is an API-backed agent record at first.

Recommended initial fields:

- `assignee_type`: `agent` or `human`
- `assignee_name`: stable display/config name, such as `codex`, `opencode`, `jason`

### Pagination

Collection routes should support:

- `page`: integer, default `1`, minimum `1`
- `per_page`: integer, default `20`, bounded by the API

Collection responses should include:

```json
{
  "items": [],
  "page": 1,
  "per_page": 20,
  "total": 0,
  "pages": 1
}
```

### Error Shape

Use structured errors consistently:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Recommended status codes:

- `400` malformed JSON/query parameters
- `404` resource not found
- `409` lease conflict, stale version, duplicate idempotency key conflict, or invalid state transition
- `422` well-formed request that fails validation

## MVP Resources

### Projects

Canonical routes:

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PATCH /api/projects/{project_id}`

Key fields:

- `id`
- `name`
- `slug`
- `project_type`
- `git_remote_url`
- `local_path`
- `environment`
- `default_agent`
- `metadata`
- `created_at`, `updated_at`, `version`

### Project Sections

Canonical routes:

- `GET /api/projects/{project_id}/sections`
- `POST /api/projects/{project_id}/sections`
- `GET /api/projects/{project_id}/sections/{section_id}`
- `PATCH /api/projects/{project_id}/sections/{section_id}`

Key fields:

- `id`
- `project_id`
- `name`
- `slug`
- `section_type`
- `description`
- `sort_order`
- `metadata`
- `created_at`, `updated_at`, `version`

### Project Status

Canonical routes:

- `GET /api/projects/{project_id}/status`
- `POST /api/projects/{project_id}/status`
- `PATCH /api/projects/{project_id}/status/{status_id}`

Key fields:

- `id`
- `project_id`
- `project_section_id`
- `status`
- `phase`
- `summary`
- `reason`
- `details`
- `source`
- `created_at`, `updated_at`, `version`

### Tasks

Canonical routes:

- `GET /api/projects/{project_id}/tasks`
- `POST /api/projects/{project_id}/tasks`
- `GET /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/claim`
- `POST /api/tasks/{task_id}/heartbeat`
- `POST /api/tasks/{task_id}/complete`
- `POST /api/tasks/{task_id}/block`

Key fields:

- `id`
- `project_id`
- `project_section_id`
- `title`
- `description`
- `status`
- `priority`
- `phase`
- `dependencies`
- `assignee_type`, `assignee_name`
- `claimed_by`, `claimed_until`, `lease_version`
- `validation_expectations`
- `completion_evidence`
- `created_at`, `updated_at`, `version`

Transition requirements:

- Claim must be atomic and must fail if an unexpired lease exists for another agent.
- Heartbeat must validate the current lease holder and extend `claimed_until`.
- Complete/block must validate lease ownership or a documented override policy.
- Every transition appends an event.
- Idempotency keys should make retries safe for agent-submitted transitions.

### Agents

Canonical routes:

- `GET /api/agents`
- `POST /api/agents`
- `GET /api/agents/{agent_id}`
- `PATCH /api/agents/{agent_id}`

Key fields:

- `id`
- `name`
- `agent_type`
- `capabilities`
- `default_model`
- `runtime_notes`
- `created_at`, `updated_at`, `version`

### Runs

Canonical routes:

- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs/{run_id}/heartbeat`
- `POST /api/runs/{run_id}/complete`
- `POST /api/runs/{run_id}/fail`

Key fields:

- `id`
- `project_id`
- `task_id`
- `agent_name`
- `status`
- `started_at`, `last_heartbeat_at`, `completed_at`
- `validation_commands`
- `validation_result`
- `summary`

### Events

Canonical routes:

- `GET /api/projects/{project_id}/events`
- `POST /api/events`

Key fields:

- `id`
- `project_id`
- `task_id`
- `run_id`
- `event_type`
- `actor_type`, `actor_name`
- `payload`
- `created_at`

### Reviews

Canonical routes:

- `GET /api/projects/{project_id}/reviews`
- `POST /api/projects/{project_id}/reviews`
- `PATCH /api/reviews/{review_id}`

Key fields:

- `id`
- `project_id`
- `source`
- `severity`
- `status`
- `finding`
- `recommendation`
- `linked_task_id`
- `created_at`, `updated_at`, `version`

## Bootstrap CLI Mapping

Bootstrap scripts should keep their current command names while their backend changes from ignored local state to API calls:

| Bootstrap command | Future API behavior |
| --- | --- |
| `task-next` | `GET /api/projects/{project_id}/tasks` with filters for unblocked/unclaimed work |
| `task-claim` | `POST /api/tasks/{task_id}/claim` |
| `task-heartbeat` | `POST /api/tasks/{task_id}/heartbeat` |
| `task-complete` | `POST /api/tasks/{task_id}/complete` |
| `task-block` | `POST /api/tasks/{task_id}/block` |
| `status-show` | `GET /api/projects/{project_id}/status` plus selected task summary |

## Open Questions

- Whether to expose flat convenience routes for the current project in addition to canonical multi-project routes.
- Whether OpenAPI should be generated from Flask code or maintained as a hand-authored spec during MVP.
- Exact status enum values for tasks, runs, reviews, and project status records.
- Whether events are implemented as database rows immediately or structured logs first with a migration path.
