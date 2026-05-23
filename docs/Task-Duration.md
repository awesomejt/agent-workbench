# Task Duration and Lease Window Sizing

How to set `estimated_duration_seconds` on tasks and how the lease window is resolved.

## Lease Window Resolution

The API resolves lease duration in three levels (first match wins):

1. **Request override** — caller passes `duration_seconds` to `/claim` or `/heartbeat`.
2. **Task estimate** — task's `estimated_duration_seconds` is set and > 0.
3. **System default** — `DEFAULT_LEASE_SECONDS = 1800` (30 minutes).

Valid range: 1–604800 seconds (1 second to 1 week). Requests outside this range return 422.

## T-Shirt Size Reference

Use these as starting points when setting `estimated_duration_seconds`. Prefer erring larger — an expired lease forces re-claim and wastes context.

| Size | Seconds | Minutes | When to use |
|---|---|---|---|
| XS | 300 | 5 | Trivial one-liner, lookup, or doc edit |
| S | 1 800 | 30 | Small well-defined task; default |
| M | 7 200 | 120 | Moderate task with some design exploration |
| L | 14 400 | 240 | Larger feature, multiple files, complex logic |
| XL | 28 800 | 480 | Major refactor, new module, or long research pass |

## Model Tier Multipliers

Local AI agents (running on hardware rather than cloud inference) tend to generate tokens more slowly. When a task's `model_tier = local`, set the estimate conservatively — an M task may effectively be an L.

| `model_tier` | Suggested multiplier |
|---|---|
| `cloud` | 1× (base estimate) |
| `local` | 1.5–2× (depending on hardware and model) |

This multiplier is a human/orchestrator judgment call at task creation time; it is not applied automatically.

## Orchestrator Guidance

When an orchestrator creates tasks:

- Set `estimated_duration_seconds` to the t-shirt size value that best fits the task.
- Apply the local multiplier if `model_tier = local`.
- Leave it `null` for trivial tasks where the 30-minute default is clearly sufficient.
- For research/discovery tasks, prefer XL — they are open-ended.

## Future Automation

Once enough task history is collected, `estimated_duration_seconds` can be derived from:
- Historical completion times grouped by `role`, `model_tier`, and t-shirt category.
- Agent-specific performance data from the `runs` table (`completed_at - started_at`).

This is a post-MVP enhancement; for now, estimates are set manually.
