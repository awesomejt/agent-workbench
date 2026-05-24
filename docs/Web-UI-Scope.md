# Web UI Scope — Post-MVP

Defines what the Agent Workbench web UI should include, its relationship to
the API/CLI, and the design decisions that need human review before
implementation begins.

## Current State

The web scaffold (`web/`) is in place:
- React 19 + Vite 6 SPA
- Express 5 production server proxying `/api/*` to the Agent Workbench API
- One working view: project list fetched from `/api/projects`
- Node 24 Dockerfile and Docker Compose `web` profile

The scaffold is the foundation. No additional views have been implemented.

## Purpose

The web UI serves two categories of users differently:

**Jason (human operator):**
- Needs to see project status at a glance without running CLI commands
- Needs to add tasks on the fly from a browser (the primary gap vs CLI)
- Needs to review agent progress, run history, and event logs
- Will use the web UI for review gates and signoff before deployments

**AI agents (secondary):**
- Do not use the web UI directly; they use the CLI and API
- Their output (runs, events, completions) is surfaced in the web UI for
  Jason's review

---

## Views to Implement

### 1. Project List (exists as scaffold)

Current state: fetches `/api/projects`, renders slug/name/phase.

Needs:
- Link each project to its detail view
- Show task counts per project (pending / in-progress / blocked)
- Show current project phase badge
- Sort/filter by phase, type, or name

### 2. Project Detail

URL: `/projects/:projectId`

Shows:
- Project metadata (slug, name, type, git remote, default agent)
- Current phase and status
- Task list grouped by section and status
- Recent events (last 10)
- Link to add a new task

### 3. Task List

URL: `/projects/:projectId/tasks`

Columns: title, phase, status, assignee, claimed_by, priority
Filters: status (pending / in_progress / blocked / completed), phase, section
Actions: click a task to see detail; button to create a new task

### 4. Task Detail

URL: `/projects/:projectId/tasks/:taskId`

Shows:
- Full task metadata (all fields)
- Lease state (claimed_by, claimed_until)
- Task relationships (blocks, blocked-by, subtasks, duplicates)
- Run history for this task
- Event log for this task
- Edit button (human can update title, description, priority, phase)
- Status transition buttons (for human-managed tasks):
  `pending → blocked`, `blocked → pending`, `in_progress → completed`

### 5. Add Task Form

URL: `/projects/:projectId/tasks/new`

Fields: title (required), description, phase, role, model_tier,
priority, section, estimated_duration_seconds

This is the primary human-input workflow. Keep it simple: title + phase
is enough to create a task; all other fields are optional.

### 6. Run List

URL: `/projects/:projectId/runs`

Shows all runs for a project: agent name, model, task title, start time,
status. Click a run for its event log and output.

### 7. Event Log

URL: `/projects/:projectId/events`

Paginated append-only log. Filterable by event_type, actor_name, date
range. Useful for auditing agent activity and reviewing decisions.

### 8. Agent Registry

URL: `/agents`

Lists registered agents, their type, model tier, and default model.
Allows Jason to register new agents or update defaults.

---

## Design Decisions for Review

These decisions need Jason's confirmation before implementation:

### 1. Single-page app vs server-rendered pages

The scaffold uses Vite + React (SPA). The alternative is server-side
rendering with Express (simpler, faster initial load, no hydration). For
the task-management use case, SPA is fine since:
- Content changes frequently (live task state)
- Jason is the only user (no SEO requirements)
- The app is internal-only (no performance budget concerns)

**Proposed: keep SPA with React. No SSR.**

### 2. Client-side routing vs server-side routes

SPA needs client-side routing for the URL structure above. React Router
v7 (or v6) is the standard choice. The Express SPA fallback (already
implemented) handles direct URL access.

**Proposed: React Router v7.**

### 3. State management

For a single-user internal tool with straightforward read-mostly data,
React Query (TanStack Query) handles server state well: caching, loading
states, background refetch, and invalidation on mutations. No global
state store (Redux/Zustand) needed at this scope.

**Proposed: TanStack Query for server state; React local state for UI.**

### 4. Component library vs custom CSS

Options:
- **Custom CSS (current)**: CSS modules, minimal dependencies. More work
  to build interactive components (tables, modals, forms).
- **Tailwind CSS**: utility-first, small bundle with purging. Good for
  rapid iteration; Jason is already familiar with the utility approach.
- **Radix UI + Tailwind**: accessible primitives + utility styling.
  Best accessibility baseline with low overhead.
- **shadcn/ui**: Radix UI + Tailwind pre-composed components. Fast to
  build forms and tables; components live in `src/components/ui/`.

**Proposed: shadcn/ui (Radix + Tailwind) for accessible components with
minimal hand-rolled CSS. This is the fastest path to a usable UI.**

### 5. Accessibility baseline

The PROJECT_BRIEF specifies: "keyboard-accessible workflows." Minimum
requirements:
- All interactive elements reachable by keyboard
- Focus indicators visible
- ARIA labels on icon-only controls
- Reasonable color contrast (WCAG AA)

**Proposed: use Radix UI primitives (included in shadcn/ui) which handle
keyboard interaction and ARIA by default.**

### 6. Authentication gate

The web UI will be open (no auth) until Option A from
`docs/Auth-IDP-Research.md` is implemented (API keys + session cookie
login form). The UI should be designed assuming it will have a login gate
eventually, but no login flow is in scope for the initial web features.

**Proposed: no auth in web UI for now; add a simple login form when API
key auth is implemented.**

### 7. Real-time updates

Task state can change while Jason is viewing the list (agent claims a
task, completes it, etc.). Options:
- **Polling**: TanStack Query refetch every 30s. Simple, no server changes.
- **Server-Sent Events**: streaming updates from the API. Requires a new
  SSE endpoint.
- **WebSockets**: bidirectional; more overhead than needed here.

**Proposed: polling via TanStack Query. 30-second refetch interval is
enough for the human review workflow. SSE/WebSockets is post-MVP.**

---

## Implementation Order

If all design decisions above are confirmed, implement in this order:

1. Install React Router + TanStack Query + Tailwind + shadcn/ui
2. Project List (enhance existing scaffold view)
3. Project Detail + Task List
4. Task Detail (read-only)
5. Add Task Form (first human-input view)
6. Task Detail edit and status transitions
7. Run List + Event Log
8. Agent Registry

Each step should be a separate task in the workbench so it can be
claimed, heartbeated, and reviewed independently.

---

## Out of Scope for Web UI MVP

- Markdown editor for task descriptions (plain textarea is fine)
- Gantt charts, burndown charts, or complex visualizations
- Multi-user collaboration features
- Mobile-optimized layout (desktop evergreen browsers only)
- Dark mode (add later if requested)
- Bulk operations (multi-select task actions)
- Notifications or alerts
- Authentication UI (deferred; see `docs/Auth-IDP-Research.md`)

---

## Files Affected When Web UI Work Begins

| File | Change |
|---|---|
| `web/package.json` | Add react-router-dom, @tanstack/react-query, tailwindcss |
| `web/src/App.jsx` | Add router + query client provider |
| `web/src/routes/` | Add route components per view |
| `web/src/components/` | Add shared UI components |
| `docs/Web-UI-Scope.md` | Update as decisions are made |
| `Makefile` | Add `web-lint` if ESLint config is added |
