# Agent Delegation Contract

Contract for delegated agent runs against Agent Workbench-managed projects.

`agent-workbench` owns task and status semantics. Workflow managers such as
Hermes, OpenCode, n8n, OpenClaw, or future runners own their own execution
model, prompts, agent definitions, transcripts, and scheduler integration.

## Lease Ownership

Each delegated run has one Agent Workbench lease owner.

- The workflow manager or primary coordinator claims one task before work
  begins.
- The claimed `AWB_AGENT` identity must stay stable for heartbeat, complete,
  and block commands.
- Specialist workers, subagents, child agents, or delegated steps do not claim,
  complete, or block the AWB task under their own names.
- If a delegated worker discovers new work, it reports it to the primary
  coordinator. The primary coordinator creates any follow-up tasks.

This keeps AWB's lease checks simple: the same `claimed_by` value owns every
state-changing lifecycle command for a run, independent of the workflow manager
used underneath.

## Generic Roles

The same coordination shape applies across Hermes, OpenCode, and other runners.

| Workbench role | Delegated responsibility |
| --- | --- |
| `orchestrator` | Runs the overall pass, delegates to specialists, and decides final outcome. |
| task/status coordination | Reads AWB task/status context and prepares completion or blocker evidence. |
| `implementer` | Produces the main code, content, or configuration change. |
| `tester` | Runs validation or quality checks and reports results. |
| `reviewer` | Performs quality review and returns prioritized findings. |
| `writer` | Updates documentation, memory, and local/session handoff notes. |

Tool-specific names are implementation details. For example, OpenCode may use
Markdown agents, while Hermes may use named workflow steps or agent profiles.

## Run Sequence

1. The workflow manager reads project status and selects the next available AWB
   task.
2. The workflow manager chooses one primary coordinator identity.
3. The primary coordinator claims the task and starts heartbeat renewal.
4. The primary coordinator reads repo-local instructions and prepares a compact
   task packet.
5. The primary coordinator delegates to specialists based on task phase, role,
   and risk.
6. The primary coordinator integrates outputs, runs final checks, and updates
   durable handoff docs when needed.
7. The primary coordinator completes or blocks the AWB task using the same
   `AWB_AGENT` identity that claimed it.

## Delegation Defaults

- `implementation` phase: task/status coordination, implementer, tester,
  reviewer, then writer when docs or memory changed.
- `testing` phase: task/status coordination, tester, optional reviewer, then
  writer for evidence updates.
- `review` phase: task/status coordination, reviewer, optional tester, then
  writer.
- Documentation-only work: task/status coordination, writer, optional reviewer.
- Discovery/design work can use the primary coordinator plus researcher/planner
  specialists when the workflow manager supports them.

## Completion Evidence

Completion evidence should include:

- Task id and concise outcome.
- Files changed or reviewed.
- Validation commands and results.
- Review/test findings addressed or left open.
- Follow-up tasks created, if any.

Blocker evidence should include the exact missing decision, credential,
dependency, external service, or unsafe operation that prevents completion.
