#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml", "requests"]
# ///
"""
Onboarding tool — scans the onboarding/ folder for Markdown files with YAML
front matter and creates tasks in the Agent Workbench API for any file whose
status is "ready".

Usage:
  uv run scripts/onboard.py [--onboarding-dir DIR] [--api-url URL] [--dry-run]

Front matter fields:
  status:     draft | ready | processed          (required)
  title:      task title                         (required)
  project:    project slug                       (required)
  phase:      discovery | design | implementation | testing | review
  role:       researcher | planner | implementer | writer | reviewer | tester | orchestrator
  model_tier: cloud | local
  priority:   integer (default 5, higher = more urgent)

Files matching *.template.md are always ignored.
On success the file is rewritten with status: processed, plus task_id and
processed_at fields added to the front matter.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    data = yaml.safe_load(text[3:end].strip()) or {}
    body = text[end + 4 :].lstrip("\n")
    return data, body


def write_front_matter(path: Path, data: dict, body: str) -> None:
    fm = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm}---\n\n{body}")


def get_project_id(api_url: str, slug: str) -> str | None:
    resp = requests.get(f"{api_url}/api/projects", timeout=10)
    resp.raise_for_status()
    for p in resp.json().get("items", []):
        if p["slug"] == slug:
            return p["id"]
    return None


def create_task(api_url: str, project_id: str, fm: dict, body: str) -> dict:
    payload: dict = {
        "title": fm["title"],
        "status": "new",
        "phase": fm.get("phase", "discovery"),
    }
    description = fm.get("description") or body.strip() or None
    if description:
        payload["description"] = description
    if fm.get("role"):
        payload["role"] = fm["role"]
    if fm.get("model_tier"):
        payload["model_tier"] = fm["model_tier"]
    if fm.get("priority") is not None:
        payload["priority"] = int(fm["priority"])

    resp = requests.post(
        f"{api_url}/api/projects/{project_id}/tasks",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def process_file(path: Path, api_url: str, dry_run: bool) -> str:
    text = path.read_text()
    fm, body = parse_front_matter(text)

    status = fm.get("status", "draft")
    if status != "ready":
        return f"skip ({status})"

    title = str(fm.get("title", "")).strip()
    project_slug = str(fm.get("project", "")).strip()

    if not title:
        return "error: missing required field 'title'"
    if not project_slug:
        return "error: missing required field 'project'"

    if dry_run:
        phase = fm.get("phase", "discovery")
        tier = fm.get("model_tier", "cloud")
        return f"dry-run: would create [{phase}/{tier}] '{title}' → project '{project_slug}'"

    project_id = get_project_id(api_url, project_slug)
    if project_id is None:
        return f"error: project slug '{project_slug}' not found in API"

    try:
        task = create_task(api_url, project_id, fm, body)
    except requests.HTTPError as e:
        return f"error: API {e.response.status_code} — {e.response.text[:120]}"

    # Rewrite front matter — update status in-place then append tracking fields
    fm["status"] = "processed"
    fm["task_id"] = task["id"]
    fm["processed_at"] = datetime.now(timezone.utc).isoformat()
    write_front_matter(path, fm, body)

    return f"created task {task['id']}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard Markdown prompts as workbench tasks")
    parser.add_argument("--onboarding-dir", default="onboarding", help="Directory to scan (default: onboarding/)")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Agent Workbench API URL")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating tasks or modifying files")
    args = parser.parse_args()

    onboarding_dir = Path(args.onboarding_dir)
    if not onboarding_dir.is_dir():
        print(f"error: onboarding directory not found: {onboarding_dir}", file=sys.stderr)
        sys.exit(1)

    api_url = args.api_url.rstrip("/")

    files = sorted(f for f in onboarding_dir.glob("*.md") if not f.name.endswith(".template.md"))

    if not files:
        print("No onboarding files found.")
        return

    errors = 0
    for f in files:
        result = process_file(f, api_url, args.dry_run)
        status_icon = "✗" if result.startswith("error") else "·"
        print(f"  {status_icon} {f.name}: {result}")
        if result.startswith("error"):
            errors += 1

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
