# Web UI Code Review — 2026-05-28

Reviewed by: claude-sonnet-4-6 via `/code-review` (high-effort, recall-biased)
Scope: commits f0f2853–4fd74f (10 commits, Web UI MVP + runs list API endpoint)
Validated: 5 CONFIRMED, 1 PLAUSIBLE findings

---

## Findings

### 1. CRITICAL — `completeTask` never sends `agent_name` → 422 on every click

**File:** `web/src/api.js:63`

`completeTask` posts only `{ evidence }` in the request body. The `/tasks/<id>/complete` endpoint unconditionally aborts with 422 if `agent_name` is absent (tasks/routes.py lines 374–376). The "Mark completed" button in TaskDetail is therefore permanently broken for all tasks.

**Fix:** Pass `agent_name` in the body. The caller should supply it (e.g. from project `default_agent` or a constant for the UI agent).

---

### 2. HIGH — No `onError` cache invalidation on 409 version conflict in StatusTransitions

**File:** `web/src/routes/TaskDetail.jsx:184`

`unblockMutation` and `completeMutation` read `task.version` from TanStack Query cache (staleTime=30s) and pass it to the PATCH/POST endpoint. The API enforces optimistic locking (tasks/routes.py lines 228–229) and returns 409 when the version is stale. Neither mutation has an `onError` or `onSettled` handler to invalidate `['task', taskId]`, so after a 409 the wrong version stays in cache indefinitely — the action button stays broken until the user manually reloads.

**Fix:** Add `onError: () => queryClient.invalidateQueries({ queryKey: ['task', taskId] })` to both mutations (or use `onSettled`).

---

### 3. HIGH — Events cache never invalidated after task status mutations

**File:** `web/src/routes/TaskDetail.jsx:196`

`completeMutation` and `unblockMutation` invalidate `['tasks', project_id]` and `['task-count', project_id]` on success, but never invalidate the events query keys. ProjectDetail uses `['events', projectId]` and ProjectRuns uses `['events', projectId, 'all']`. Neither query has `refetchInterval` set, so the event log shows pre-mutation state indefinitely.

**Fix:** Also invalidate `['events', task.project_id]` in both mutations' `onSuccess` handlers.

---

### 4. MEDIUM — `fetchRuns` discards pagination envelope; ProjectRuns shows wrong count

**File:** `web/src/api.js:100`

`fetchRuns` returns `d.items ?? []`, silently dropping `total`, `pages`. ProjectRuns displays `runs.length` as the count badge. With a default `per_page=50`, any project with 51+ runs silently shows truncated results with no warning and no way to paginate.

**Fix:** Return the full envelope `{ items, total, page, pages }` from `fetchRuns`, update the call site to read `.items`, and display `total` in the count badge.

---

### 5. MEDIUM — N+1 HTTP requests in ProjectList (4 per row × N projects)

**File:** `web/src/routes/ProjectList.jsx:26`

Each `ProjectRow` fires 4 independent HTTP requests on mount: 1 `fetchProjectStatus` + 3 `fetchTaskCount` calls (pending/in_progress/blocked). A 20-project list triggers 80 parallel requests, repeating every 30 seconds. There is no batch/summary API.

**Options:**
- Add a `GET /api/projects/:id/summary` endpoint returning status + task counts in one query.
- Or reduce to 1 `fetchTasks` call per row and derive counts client-side.
- Immediate mitigation: increase `staleTime` / `refetchInterval` for these queries to reduce repeat cost.

---

### 6. LOW — `RelationshipsSection` uses raw `fetch()` instead of `apiFetch`

**File:** `web/src/routes/TaskDetail.jsx:33`

The inline `queryFn` calls `fetch('/api/tasks/${taskId}/relationships')` directly rather than going through the `apiFetch` helper in `api.js`. Currently `apiFetch` adds no headers, so there is no present-tense bug — but any future addition of auth headers or base-URL logic to `apiFetch` will silently skip this call site.

**Fix:** Export a `fetchRelationships(taskId)` function from `api.js` using `apiFetch` and use it here.

---

## What was NOT a bug (refuted candidates)

- `except ValueError, TypeError:` in runs/routes.py — valid Python 3 tuple-catch syntax; works correctly.
- `list_runs` cross-project `task_id` — service filters by both `project_id` and `task_id`; returning empty is correct.
