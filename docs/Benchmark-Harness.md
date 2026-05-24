# Benchmark Harness — Design

Design for `benchmark-harness`, a separate project providing structured AI agent
evaluation. It consumes Agent Workbench as coordination infrastructure.

## Purpose

`benchmark-harness` runs a fixed set of prompts against one or more
agent/model combinations, scores each response against defined rubrics, and
produces comparison reports. The goal is to make model and agent regressions
visible before they affect production work, and to give Jason a factual basis
for choosing agents and models for specific task types.

## Separation from Agent Workbench

`benchmark-harness` is a **separate Git repository** and a **registered
project inside Agent Workbench**. It is not a module of the workbench API.

| Concern | Owner |
|---|---|
| Task coordination (claim, heartbeat, complete) | Agent Workbench API + `awb` CLI |
| Prompt library (curated eval inputs) | `benchmark-harness` |
| Scoring rubrics (how to grade a response) | `benchmark-harness` |
| Evaluation run execution | `benchmark-harness` |
| Results storage | `benchmark-harness` own database |
| Comparison reports | `benchmark-harness` |

The workbench tracks **that** an evaluation ran and **whether** it succeeded.
The benchmark-harness stores **what** was scored and **how well**.

## Core Concepts

### Benchmark Suite

A named, versioned collection of prompts targeting a specific capability area.

| Field | Type | Description |
|---|---|---|
| `id` | uuid | Stable identity across suite versions |
| `slug` | string | e.g. `code-generation-v1` |
| `capability` | string | e.g. `code-generation`, `reasoning`, `api-usage` |
| `description` | text | What this suite measures |
| `version` | int | Increments on structural changes |

### Prompt

A single evaluation input.

| Field | Type | Description |
|---|---|---|
| `id` | uuid | |
| `suite_id` | uuid | Parent suite |
| `category` | string | Sub-category within the capability |
| `difficulty` | enum | `easy \| medium \| hard` |
| `input` | text | The prompt text sent to the agent |
| `expected_output_type` | enum | `text \| code \| json \| tool_calls` |
| `rubric_id` | uuid | Which rubric grades this prompt |
| `reference_answer` | text | Optional ground-truth answer for exact/llm comparison |

### Rubric

A grading strategy applied to agent output.

| Rubric type | How it works |
|---|---|
| `exact_match` | Response equals reference after normalization |
| `regex_match` | Response matches one or more patterns |
| `llm_judge` | A second LLM call rates the response 0–100 against criteria |
| `test_execution` | Response is extracted as code and test cases are run against it |
| `tool_call_check` | Verifies a required tool was called with expected arguments |
| `human` | Deferred; marks the prompt as requiring manual review |

Rubrics are stored as configuration (YAML/JSON) in the benchmark-harness repo,
not in a database. They are loaded at evaluation time.

### Evaluation Run

One run of a suite against a specific agent and model.

| Field | Type | Description |
|---|---|---|
| `id` | uuid | |
| `suite_id` | uuid | Which suite was evaluated |
| `agent_name` | string | e.g. `claude-code`, `opencode` |
| `model_id` | string | e.g. `claude-sonnet-4-6` |
| `awb_run_id` | uuid | Corresponding run record in Agent Workbench |
| `started_at` | datetime | |
| `finished_at` | datetime | |
| `status` | enum | `running \| completed \| failed` |
| `summary` | jsonb | Aggregate scores (pass rate, avg score, latency p50/p95) |

### Score

A single prompt result within an evaluation run.

| Field | Type | Description |
|---|---|---|
| `id` | uuid | |
| `run_id` | uuid | Parent evaluation run |
| `prompt_id` | uuid | Which prompt was evaluated |
| `raw_response` | text | Full agent output |
| `score` | int | 0–100; rubric-specific meaning |
| `passed` | bool | Score ≥ pass threshold for this rubric |
| `latency_ms` | int | Time from request to response |
| `cost_usd` | decimal | Estimated API cost (null if unavailable) |
| `rubric_notes` | text | Explanation from llm_judge or test runner |
| `created_at` | datetime | |

## Integration with Agent Workbench

### Workbench Project Registration

`benchmark-harness` registers itself as a project in Agent Workbench using
project type `automation` with a `local_path` pointing to its repo.

### Per-Suite Tasks

When a suite run is initiated, the harness creates one task per prompt in the
workbench under the `benchmark-harness` project. Each task carries:

- `title`: `[suite-slug] Evaluate prompt <prompt_id>`
- `phase`: `testing`
- `role`: `tester`
- `model_tier`: `cloud` (most benchmarks require cloud model quality)

The evaluation runner then claims tasks, evaluates, and marks them complete or
blocked via `awb`. This enables:

- Distributed evaluation: multiple runners can process the same suite in parallel
- Resume on crash: uncompleted tasks re-enter the queue after lease expiry
- Evidence trail: completion notes carry the score summary

### Minimal Integration (MVP)

For the initial MVP, the integration can be lighter: one task per evaluation
run (not one per prompt), with the score summary attached as completion
evidence. Per-prompt granularity can be added later.

## Data Model Diagram

```
benchmark_suites ──┐
                   ├──< prompts >──── rubric configs (YAML files)
                   │
evaluation_runs ───┘
       │
       └──< scores
```

Relationships in SQL:
- `prompts.suite_id → benchmark_suites.id`
- `evaluation_runs.suite_id → benchmark_suites.id`
- `scores.run_id → evaluation_runs.id`
- `scores.prompt_id → prompts.id`

## Comparison Reports

A comparison report aggregates multiple evaluation runs sharing the same suite
slug across different agents or models. Output is a Markdown or HTML table:

```
Suite: code-generation-v1

| Agent         | Model               | Pass Rate | Avg Score | p50 latency | Cost/run |
|---|---|---|---|---|---|
| claude-code   | claude-sonnet-4-6   | 87%       | 82        | 1.2s        | $0.43    |
| opencode      | Qwen3.5-27B         | 61%       | 58        | 3.8s        | $0.02    |
| claude-code   | claude-opus-4-7     | 94%       | 91        | 2.1s        | $1.87    |
```

Reports are generated as static files (Markdown + optional HTML). They are
committed to a `reports/` directory inside the benchmark-harness repo and can
optionally be stored as Agent Workbench events for visibility in future web UI.

## Tech Stack

Following the same conventions as Agent Workbench:

| Concern | Choice |
|---|---|
| Language | Python 3.14 |
| Package manager | `uv` |
| API (if any) | Flask |
| Database | PostgreSQL (same `postgresql.taylor.lan` for prod, local container for dev) |
| Migrations | Alembic |
| Config | Environment variables (`APP_ENV`, `DATABASE_URL`) + `.env` for local |
| CLI | Python Click or reuse `awb` for task lifecycle |
| LLM calls | Direct HTTP / Anthropic SDK |

For the MVP, the CLI runner (`bench run`, `bench report`) is the primary
interface. A web UI for browsing results is post-MVP.

## Proposed Project Structure

```
benchmark-harness/
├── api/                    # Optional Flask API for results query
│   └── src/benchmark_harness/
├── cli/                    # Python Click CLI: bench run, bench report
├── suites/                 # YAML benchmark suite definitions
│   └── code-generation-v1.yaml
├── rubrics/                # YAML rubric configs
│   └── llm-judge-default.yaml
├── reports/                # Generated comparison reports
├── tests/
├── docs/
├── docker-compose.yaml
├── Makefile
└── AGENTS.md
```

## CLI Commands (MVP)

```bash
# List available suites
bench suite list

# Run a suite against an agent+model
bench run --suite code-generation-v1 --agent claude-code --model claude-sonnet-4-6

# Generate a comparison report for a suite
bench report --suite code-generation-v1 --output reports/code-gen-comparison.md

# Show recent run results
bench results --suite code-generation-v1 --last 5
```

## MVP Scope

The MVP for `benchmark-harness` is the minimum that makes one comparison
meaningful:

1. One benchmark suite (`code-generation-v1`) with 10–20 prompts.
2. Two rubric types: `exact_match` and `llm_judge`.
3. A CLI runner that evaluates prompts sequentially (parallel later).
4. Results stored in a local SQLite database for simplicity (PostgreSQL later).
5. A plain Markdown comparison report.
6. Agent Workbench integration via one task per evaluation run (not per prompt).

Prompt distribution, parallel evaluation, per-prompt task granularity, HTML
reports, and a web UI are all post-MVP.

## Open Questions

- **Suite authorship**: who writes and maintains prompts? Jason, agents, or
  both? Proposed: agents draft, Jason reviews before merge.
- **LLM-as-judge model**: which model grades responses? Proposed: default to
  the best available cloud model at run time; configurable per rubric.
- **Cost tracking**: some providers expose token counts; others do not. Proposed:
  store `null` when unavailable, compute from known pricing when possible.
- **Suite versioning policy**: when a prompt changes, old scores for that prompt
  are no longer comparable. Proposed: increment the suite `version` on any
  structural change; comparisons are only valid within the same version.
