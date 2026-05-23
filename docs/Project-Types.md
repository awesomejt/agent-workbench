# Project Types

Vocabulary for the `project_type` field on projects. Types influence default sections, phase expectations, and agent role interpretation.

## Type Enum

| `project_type` | Description |
|---|---|
| `code` | Software development: services, tools, libraries, APIs, CLIs |
| `course` | Educational course or curriculum: lessons, exercises, assessments |
| `content` | Content creation: books, articles, blog posts, video scripts, docs sets |
| `research` | Investigation, spike, white paper, or experiment |
| `infrastructure` | DevOps and operations: deployment, provisioning, configuration |
| `other` | Does not fit a defined type |

Default: `code`.

## Default Sections by Type

Default sections are suggested starting points. Projects may add, rename, or omit sections.

| Type | Suggested sections |
|---|---|
| `code` | `api`, `cli`, `frontend`, `tests`, `docs`, `deployment` |
| `course` | `curriculum`, `lessons`, `exercises`, `assessments`, `supplements` |
| `content` | `outline`, `drafts`, `revisions`, `published` |
| `research` | `discovery`, `analysis`, `report`, `references` |
| `infrastructure` | `design`, `configuration`, `deployment`, `validation` |
| `other` | none — define per project |

## Phase Expectations by Type

All types use the same five-phase ordinal (`discovery → design → implementation → testing → review`). What "done" looks like in each phase differs by type:

### `code`
- **discovery:** technology research, spike branches, options analysis
- **design:** architecture decisions, API contracts, task breakdown
- **implementation:** working code that passes tests
- **testing:** integration tests, edge case coverage, performance baselines
- **review:** code review (correctness, security, maintainability), release prep

### `course`
- **discovery:** topic research, audience analysis, learning objective drafts
- **design:** curriculum outline, lesson plan, assessment design
- **implementation:** lesson content, exercises, answer keys
- **testing:** fact-check, editorial review, learner walkthrough
- **review:** subject-matter expert signoff, publication prep

### `content`
- **discovery:** source research, audience analysis, angle exploration
- **design:** outline, structure decisions
- **implementation:** draft writing
- **testing:** fact-check, editorial pass
- **review:** final edit, publication approval

### `research`
- **discovery:** problem framing, source identification
- **design:** research plan, methodology
- **implementation:** investigation, experiments, data collection
- **testing:** peer review, validation of findings
- **review:** final recommendation, stakeholder signoff

### `infrastructure`
- **discovery:** current-state audit, requirements gathering
- **design:** architecture, runbook drafts, security review
- **implementation:** configuration, provisioning scripts
- **testing:** deployment validation, rollback test
- **review:** runbook review, operational readiness signoff

## Default Agent Role → Model Tier

These defaults apply to all project types. Override in the project's `AGENTS.md` when the defaults do not fit.

| Phase | Default model_tier | Rationale |
|---|---|---|
| `discovery` | `cloud` | broad knowledge, open-ended research |
| `design` | `local` | well-structured planning, low ambiguity |
| `implementation` | `local` | defined tasks, deterministic execution |
| `testing` | `local` | validation against known criteria |
| `review` | `cloud` | judgment, security reasoning, nuance |

For role interpretation by project type, see `AGENTS.md` (Agent Roles and Model Tiers section) and `docs/Agent-Roles.md`.
