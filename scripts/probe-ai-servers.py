#!/usr/bin/env python3
"""Probe all registered AI servers and update their availability status in the workbench.

Designed to run on a schedule (e.g., cron every 5 minutes):
    */5 * * * * AWB_API_URL=http://localhost:8000 python /path/to/probe-ai-servers.py

Environment variables:
    AWB_API_URL   Workbench API base URL (default: http://localhost:8000)
    PROBE_TIMEOUT Seconds to wait per server health check (default: 5)

# TODO: extend to also fetch and store the model list for each server:
#   - Ollama:         GET /api/tags  → {models: [{name, ...}]}
#   - LiteLLM/oMLX:  GET /v1/models → {data: [{id, ...}]}
#   Store in server's metadata field so agents can filter by model availability.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime

AWB_API_URL = os.environ.get("AWB_API_URL", "http://localhost:8000").rstrip("/")
PROBE_TIMEOUT = int(os.environ.get("PROBE_TIMEOUT", "5"))

# Health endpoint per server type.
# Returns (path, expect_json) — if expect_json, a 200 with any JSON body means up.
_HEALTH_PATHS: dict[str, str] = {
    "ollama": "/api/tags",       # returns {"models": [...]}
    "litellm": "/health",        # returns {"status": "healthy", ...}
    "omlx": "/v1/models",        # OpenAI-compatible: returns {"data": [...]}
    "openai_compat": "/v1/models",
}
_HEALTH_FALLBACK = "/health"


def _api_get(path: str) -> dict:
    req = urllib.request.Request(f"{AWB_API_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _api_patch(path: str, body: dict) -> None:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{AWB_API_URL}{path}",
        data=data,
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10):
        pass


def _probe(server: dict) -> tuple[str, str | None]:
    """Return (status, error_message). status is 'up' or 'down'."""
    base_url = server["url"].rstrip("/")
    server_type = server["server_type"]
    health_path = _HEALTH_PATHS.get(server_type, _HEALTH_FALLBACK)
    url = f"{base_url}{health_path}"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            if resp.status == 200:
                return "up", None
            return "down", f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return "down", f"HTTP {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return "down", str(exc.reason)
    except TimeoutError:
        return "down", f"timed out after {PROBE_TIMEOUT}s"
    except Exception as exc:  # noqa: BLE001
        return "down", str(exc)


def main() -> int:
    print(f"[{datetime.now(UTC).isoformat()}] probe-ai-servers starting — {AWB_API_URL}")

    try:
        result = _api_get("/api/ai-servers?per_page=100")
    except Exception as exc:
        print(f"ERROR: could not reach workbench API: {exc}", file=sys.stderr)
        return 1

    servers = result.get("items", [])
    if not servers:
        print("No servers registered. Add servers via: awb ai-server create ...")
        return 0

    errors = 0
    for server in servers:
        status, error = _probe(server)
        symbol = "✓" if status == "up" else "✗"
        print(f"  {symbol} {server['name']} ({server['server_type']}) [{server['url']}] → {status}")
        if error:
            print(f"      {error}")

        patch_body: dict = {
            "status": status,
            "version": server["version"],
        }
        if error:
            patch_body["last_error"] = error

        try:
            _api_patch(f"/api/ai-servers/{server['id']}", patch_body)
        except Exception as exc:
            print(f"      WARNING: failed to update server record: {exc}", file=sys.stderr)
            errors += 1

    print(f"Done. {len(servers)} server(s) probed, {errors} update error(s).")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
