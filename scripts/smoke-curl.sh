#!/usr/bin/env bash
# Smoke checks against a running Agent Workbench API.
# Usage: ./scripts/smoke-curl.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000

set -euo pipefail

BASE="${1:-http://localhost:8000}"
PASS=0
FAIL=0

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

echo "Smoke checks → $BASE"
echo ""

# Health
_check "GET /health returns 200"           200 "$BASE/health"

# Projects — list and create
_check "GET /api/projects returns 200"     200 "$BASE/api/projects"
_check "POST /api/projects creates project" 201 "$BASE/api/projects" POST \
    '{"name":"Smoke Test Project","slug":"smoke-test","project_type":"generic","environment":"local"}'

# Agents — list and create
_check "GET /api/agents returns 200"       200 "$BASE/api/agents"
_check "POST /api/agents creates agent"    201 "$BASE/api/agents" POST \
    '{"name":"smoke-agent","agent_type":"cli"}'

# Events — list (no project required for global endpoint)
_check "POST /api/events appends event"    201 "$BASE/api/events" POST \
    '{"event_type":"smoke.check","actor_type":"script","actor_name":"smoke-curl"}'

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
