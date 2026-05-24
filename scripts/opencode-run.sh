#!/usr/bin/env bash
# scripts/opencode-run.sh
#
# Claims the next available Agent Workbench task and runs one focused OpenCode
# session against this repository.
#
# Usage:
#   ./scripts/opencode-run.sh [--dry-run] [--verbose] [--model <model>] [--agent <agent>]
#
# Environment:
#   AWB_API_URL   Agent Workbench API base URL (default: http://localhost:8000)
#   AWB_PROJECT   Project slug (default: agent-workbench)
#   AWB_AGENT     Agent name reported to the workbench (default: opencode)
#   OPENCODE_MODEL  Model passed to opencode run
#   OPENCODE_AGENT  OpenCode agent profile (default: yolo)
#   OPENCODE_DRY_RUN  Set to 1 to print intended actions without invoking opencode
#   OPENCODE_LOG_FILE Optional path to append log output
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

AWB="${AWB_CLI:-${REPO_ROOT}/cli/builds/awb}"
AWB_API_URL="${AWB_API_URL:-http://localhost:8000}"
AWB_PROJECT="${AWB_PROJECT:-agent-workbench}"
AWB_AGENT="${AWB_AGENT:-opencode}"

MODEL="${OPENCODE_MODEL:-}"
OC_AGENT="${OPENCODE_AGENT:-yolo}"
DRY_RUN="${OPENCODE_DRY_RUN:-0}"
VERBOSE=0

log() {
  local ts
  ts="$(date '+%Y-%m-%dT%H:%M:%S')"
  local msg="[opencode-run] ${ts} $*"
  echo "$msg" >&2
  if [[ -n "${OPENCODE_LOG_FILE:-}" ]]; then
    echo "$msg" >> "$OPENCODE_LOG_FILE"
  fi
}

usage() {
  cat <<'USAGE'
Usage: opencode-run.sh [--dry-run] [--verbose] [--model <model>] [--agent <agent>]

Claims the next available task from Agent Workbench and runs one focused
OpenCode session targeting this repository. Exits 0 with no work done if
no task is available.

Options:
  --dry-run         Print the resolved task and prompt without invoking opencode.
  --verbose         Log resolved parameters before running.
  --model <model>   Override OPENCODE_MODEL.
  --agent <agent>   Override OPENCODE_AGENT (OpenCode agent profile).
  -h, --help        Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=1; shift ;;
    --verbose)    VERBOSE=1; shift ;;
    --model)      MODEL="$2"; shift 2 ;;
    --agent)      OC_AGENT="$2"; shift 2 ;;
    -h|--help)    usage; exit 0 ;;
    *)            echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# ── Lock ──────────────────────────────────────────────────────────────────────

repo_key="$(printf '%s' "$REPO_ROOT" | tr '/: ' '---' | tr -cd '[:alnum:]_.-')"
LOCK_DIR="${OPENCODE_LOCK_DIR:-${TMPDIR:-/tmp}/opencode-run-${repo_key}.lock}"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "Another run is active for ${REPO_ROOT}; lock exists at ${LOCK_DIR}. Exiting."
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT INT TERM

# ── Preflight ────────────────────────────────────────────────────────────────

if [[ ! -x "$AWB" ]]; then
  log "ERROR: awb CLI not found at ${AWB}. Run 'make build-cli' first."
  exit 1
fi

if ! "$AWB" --api-url "$AWB_API_URL" --project "$AWB_PROJECT" task list > /dev/null 2>&1; then
  log "ERROR: Agent Workbench API not reachable at ${AWB_API_URL}. Start the API before running."
  exit 1
fi

# ── Claim next task ──────────────────────────────────────────────────────────

log "Fetching next available task from ${AWB_API_URL} (project: ${AWB_PROJECT})..."

TASK_JSON="$(
  AWB_API_URL="$AWB_API_URL" AWB_PROJECT="$AWB_PROJECT" AWB_AGENT="$AWB_AGENT" \
    "$AWB" task next --output json 2>/dev/null || echo "{}"
)"

TASK_ID="$(echo "$TASK_JSON" | python3 -c "import json,sys; t=json.load(sys.stdin); print(t.get('id',''))" 2>/dev/null || true)"
TASK_TITLE="$(echo "$TASK_JSON" | python3 -c "import json,sys; t=json.load(sys.stdin); print(t.get('title',''))" 2>/dev/null || true)"
TASK_PHASE="$(echo "$TASK_JSON" | python3 -c "import json,sys; t=json.load(sys.stdin); print(t.get('phase',''))" 2>/dev/null || true)"
TASK_DESC="$(echo "$TASK_JSON"  | python3 -c "import json,sys; t=json.load(sys.stdin); print(t.get('description') or '')" 2>/dev/null || true)"

if [[ -z "$TASK_ID" ]]; then
  log "No available tasks. Nothing to do."
  exit 0
fi

log "Claiming task ${TASK_ID}: ${TASK_TITLE}"

if [[ "$DRY_RUN" != "1" ]]; then
  AWB_API_URL="$AWB_API_URL" AWB_PROJECT="$AWB_PROJECT" AWB_AGENT="$AWB_AGENT" \
    "$AWB" task claim "$TASK_ID" --agent "$AWB_AGENT" > /dev/null
fi

# ── Build focused prompt ─────────────────────────────────────────────────────

AWB_ENV="AWB_API_URL=${AWB_API_URL} AWB_PROJECT=${AWB_PROJECT} AWB_AGENT=${AWB_AGENT}"
AWB_BIN="${REPO_ROOT}/cli/builds/awb"

PROMPT="$(cat <<PROMPT
# Focused Task Run

You have been given exactly one task to complete. Do not pick additional work.

## Your Task

Task ID:    ${TASK_ID}
Phase:      ${TASK_PHASE}
Title:      ${TASK_TITLE}
${TASK_DESC:+Description: ${TASK_DESC}}

## Agent Workbench Commands

Use these commands to manage the task lifecycle. Set the env vars or pass as flags.

    export ${AWB_ENV}
    AWB=${AWB_BIN}

    # Renew your lease every few minutes while working
    \$AWB task heartbeat ${TASK_ID} --agent ${AWB_AGENT}

    # When done
    \$AWB task complete ${TASK_ID} --agent ${AWB_AGENT} --evidence "<summary>"

    # If blocked
    \$AWB task block ${TASK_ID} --agent ${AWB_AGENT} --reason "<reason>"

## Preflight

1. Confirm working directory with \`pwd\`.
2. Check \`git status --short --branch\` before editing.
3. Read \`AGENTS.md\`, \`PROJECT_BRIEF.md\`, and any docs relevant to the task before starting.

## Work Discipline

- Make the smallest correct change that completes this task.
- Keep public contracts (API, CLI, docs, tests) aligned.
- Validate the change. Record any validation gaps or blockers.
- Commit completed work when validation passes.
- Mark the task complete or blocked before exiting.
PROMPT
)"

if [[ "$VERBOSE" == "1" || "$DRY_RUN" == "1" ]]; then
  log "Resolved parameters:"
  log "  TASK_ID=${TASK_ID}"
  log "  TASK_TITLE=${TASK_TITLE}"
  log "  OC_AGENT=${OC_AGENT}"
  log "  MODEL=${MODEL:-<default>}"
  log "  REPO_ROOT=${REPO_ROOT}"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  log "Dry run — prompt that would be sent to OpenCode:"
  printf -- '----- BEGIN PROMPT -----\n%s\n----- END PROMPT -----\n' "$PROMPT" >&2
  exit 0
fi

# ── Run OpenCode ─────────────────────────────────────────────────────────────

log "Starting OpenCode (agent=${OC_AGENT}${MODEL:+, model=${MODEL}}) on task ${TASK_ID}."

oc_args=(--agent "$OC_AGENT" --dir "$REPO_ROOT")
if [[ -n "$MODEL" ]]; then
  oc_args+=(--model "$MODEL")
fi

opencode run "${oc_args[@]}" "$PROMPT"
log "OpenCode run finished."
