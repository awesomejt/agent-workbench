# State Machines

Authoritative reference for all status and phase state machines in Agent Workbench. These reflect the implemented behavior in `api/src/agent_workbench/`.

## Task Assignment and Claiming

Tasks have two distinct concepts of "who is working on this":

### Assignment (`assignee_type`, `assignee_name`)

- Set by an orchestrator or human on task creation or via PATCH.
- A *routing hint* — indicates who is expected or intended to work on the task.
- Not enforced at the coordination level; any available agent may still claim the task.
- `assignee_type`: `agent` or `human`.
- `assignee_name`: stable identifier such as `opencode`, `claude-local`, `jason`.
- `null` means unassigned; open to any available agent.

**Human-assigned tasks** (`assignee_type=human`) signal that a person needs to review, validate, or take an action. Humans do not use the claim/heartbeat mechanism. An agent may complete a human-assigned task when acting on the human's documented behalf.

### Claiming (`claimed_by`, `claimed_until`, `lease_version`)

- Set **atomically** by `POST /api/tasks/{id}/claim`; enforced by targeted UPDATE with rowcount check.
- Only one agent may hold a live lease at a time.
- The lease holder must heartbeat before `claimed_until` or the lease expires and the task becomes available again.
- Claiming does not validate against `assignee_name` — assignment is informational only.

### Why two concepts?

Assignment supports planning and routing (orchestrators can pre-assign work to specific agents or mark tasks for human attention) without coupling it to the coordination-critical lease mechanism. The lease is the authoritative concurrency primitive; assignment is metadata.

### Fields summary

| Field | Purpose | Set by |
|---|---|---|
| `assignee_type` | Agent or human responsibility | orchestrator, PATCH |
| `assignee_name` | Intended worker identity | orchestrator, PATCH |
| `claimed_by` | Active lease holder | `/claim` endpoint only |
| `claimed_until` | Lease expiry timestamp | `/claim`, `/heartbeat` |
| `lease_version` | Monotonic claim counter | `/claim` (increments) |

## Task Status

**States:** `new`, `pending`, `in_progress`, `blocked`, `completed`, `rejected`, `duplicate`

**Create constraints:** tasks may only be created with status `new` or `pending`.

**PATCH transitions (direct status field updates):**

| From | To | Notes |
|---|---|---|
| `new` | `pending` | orchestrator marks task ready to claim |
| `new` | `rejected` | orchestrator rejects out-of-scope or invalid task |
| `new` | `duplicate` | orchestrator marks duplicate; create a `duplicates` relationship |
| `blocked` | `pending` | human or orchestrator resets a blocked task |

**Action endpoint transitions:**

| Action | From | To | Guard |
|---|---|---|---|
| `POST /claim` | `pending` | `in_progress` | no unexpired lease for another agent; sets `claimed_by`, `claimed_until`, increments `lease_version` |
| `POST /claim` (recovery) | `in_progress` | `in_progress` | lease has expired; replaces the previous agent's lease |
| `POST /heartbeat` | `in_progress` | `in_progress` | caller must be current lease holder; extends `claimed_until` |
| `POST /complete` | `in_progress` | `completed` | caller must be current lease holder; clears lease fields |
| `POST /block` | `in_progress` | `blocked` | caller must be current lease holder; clears lease fields |

**Terminal states:** `completed`, `rejected`, `duplicate` — no transitions out.

**Diagram:**

```
            ┌──────────────────────────────────┐
            │              new                 │
            └──────┬─────────────┬─────────────┘
                   │ PATCH       │ PATCH
              pending          rejected / duplicate
               │  ▲
        /claim │  │ PATCH (blocked→pending)
               ▼  │
           in_progress ◄─── /heartbeat (extend lease)
            │        │
     /block │        │ /complete
            ▼        ▼
         blocked   completed
            │
   PATCH    │
  (→pending)┘
```

---

## Project Phase (Forward-Only High-Water Mark)

**Phases (ordinal order):**

| Ordinal | Phase |
|---|---|
| 1 | `discovery` |
| 2 | `design` |
| 3 | `implementation` |
| 4 | `testing` |
| 5 | `review` |

**Rules:**

- Phase is tracked as an append-only sequence of `project_statuses` rows, not a single mutable field.
- The current phase is the `phase` of the most recent `project_statuses` record.
- Phase only ever advances — it never moves backward.
- **Auto-advance on claim:** when a task is claimed, if `task.phase` ordinal > current project phase ordinal, a new `project_statuses` row is inserted automatically with `source = "auto-claim"`.
- Manual status records may also record a phase; these are treated the same as auto-advance records.
- Multiple concurrent claims at the same phase produce only one new status record (the second claim finds the phase already at the task level and skips insertion).

---

## Run Status

**States:** `running` (initial), `completed`, `failed`

**Transitions:**

| Action | From | To | Guard |
|---|---|---|---|
| `POST /api/runs` (create) | — | `running` | auto-set on creation |
| `POST /api/runs/{id}/heartbeat` | `running` | `running` | extends `last_heartbeat_at` |
| `POST /api/runs/{id}/complete` | `running` | `completed` | sets `completed_at` |
| `POST /api/runs/{id}/fail` | `running` | `failed` | sets `completed_at`, records failure reason |

**Terminal states:** `completed`, `failed`

---

## Review Finding Status

**States:** `open`, `resolved`, `deferred`

**Transitions:** any → any via `PATCH /api/reviews/{review_id}` (no strict guard; reviewer judgment applies).

**Severities (not a state machine, informational):** `critical`, `high`, `medium`, `low`, `info`

---

## Project Status Record

`project_statuses` rows use a `status` field (workflow state) and a `phase` field (lifecycle position). These are independent.

**`status` values:** `active`, `paused`, `blocked`, `working`, `error`, `stopped`

These are not formally guarded at the API level — callers may set any value. The intended workflow is documented in `AGENTS.md` under "Status Workflow".

**`phase` values:** same five-phase enum as tasks (see Project Phase above).
