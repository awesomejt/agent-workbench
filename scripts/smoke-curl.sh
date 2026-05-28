#!/usr/bin/env bash
# Smoke checks against a running Agent Workbench API.
# Usage: ./scripts/smoke-curl.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000
#
# Creates ephemeral resources with a run-specific suffix so the script is
# safe to run multiple times against the same database.

set -euo pipefail

BASE="${1:-http://localhost:8000}"
PASS=0
FAIL=0
RUN_ID="$(date +%s)"

_check() {
    local label="$1"
    local expected_status="$2"
    local url="$3"
    local method="${4:-GET}"
    local body="${5:-}"

    local args=(-s -o /dev/null -w "%{http_code}" -X "$method")
    if [[ -n "$body" ]]; then
        args+=(-H "Content-Type: application/json" -d "$body")
    fi

    local actual
    actual=$(curl "${args[@]}" "$url" 2>/dev/null)

    if [[ "$actual" == "$expected_status" ]]; then
        echo "  PASS  [$actual] $label"
        (( PASS++ )) || true
    else
        echo "  FAIL  [got $actual, want $expected_status] $label"
        (( FAIL++ )) || true
    fi
}

# Post and return "STATUS BODY" on two lines (status first, then JSON body).
_post_capture() {
    local url="$1"
    local body="$2"
    local tmp
    tmp=$(mktemp)
    local sc
    sc=$(curl -s -o "$tmp" -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$body" "$url" 2>/dev/null)
    echo "$sc"
    cat "$tmp"
    rm -f "$tmp"
}

echo "Smoke checks → $BASE  (run=$RUN_ID)"
echo ""

# Health
_check "GET /health returns 200" 200 "$BASE/health"

# Projects — list and create (unique slug per run)
_check "GET /api/projects returns 200" 200 "$BASE/api/projects"
PROJECT_SLUG="smoke-$RUN_ID"
PROJECT_RESP=$(_post_capture "$BASE/api/projects" \
    "{\"name\":\"Smoke $RUN_ID\",\"slug\":\"$PROJECT_SLUG\",\"project_type\":\"code\",\"environment\":\"local\"}")
PROJECT_STATUS=$(echo "$PROJECT_RESP" | head -1)
PROJECT_ID=$(echo "$PROJECT_RESP" | tail -n +2 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
if [[ "$PROJECT_STATUS" == "201" && -n "$PROJECT_ID" ]]; then
    echo "  PASS  [201] POST /api/projects creates project (id=${PROJECT_ID:0:8}…)"
    (( PASS++ )) || true
else
    echo "  FAIL  [got $PROJECT_STATUS, want 201] POST /api/projects creates project"
    (( FAIL++ )) || true
fi

# Tasks — create under new project, then full lifecycle
if [[ -n "$PROJECT_ID" ]]; then
    TASK_RESP=$(_post_capture "$BASE/api/projects/$PROJECT_ID/tasks" \
        '{"title":"smoke task","status":"pending","phase":"testing"}')
    TASK_STATUS=$(echo "$TASK_RESP" | head -1)
    TASK_ID=$(echo "$TASK_RESP" | tail -n +2 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    if [[ "$TASK_STATUS" == "201" && -n "$TASK_ID" ]]; then
        echo "  PASS  [201] POST /api/projects/{id}/tasks creates task (id=${TASK_ID:0:8}…)"
        (( PASS++ )) || true

        _check "POST /api/tasks/{id}/claim returns 200" 200 \
            "$BASE/api/tasks/$TASK_ID/claim" POST \
            '{"agent_name":"smoke-agent"}'

        _check "POST /api/tasks/{id}/complete returns 200" 200 \
            "$BASE/api/tasks/$TASK_ID/complete" POST \
            '{"agent_name":"smoke-agent","evidence":"smoke test passed"}'
    else
        echo "  FAIL  [got $TASK_STATUS, want 201] POST /api/projects/{id}/tasks creates task"
        (( FAIL++ )) || true
    fi
fi

# Agents — list and create (unique name per run)
_check "GET /api/agents returns 200" 200 "$BASE/api/agents"
_check "POST /api/agents creates agent" 201 "$BASE/api/agents" POST \
    "{\"name\":\"smoke-agent-$RUN_ID\",\"agent_type\":\"cli\"}"

# Events — append
_check "POST /api/events appends event" 201 "$BASE/api/events" POST \
    '{"event_type":"smoke.check","actor_type":"script","actor_name":"smoke-curl"}'

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
