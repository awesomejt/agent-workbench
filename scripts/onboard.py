#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml", "requests"]
# ///
"""
Onboarding tool — scans the onboarding/ folder for Markdown files with YAML
front matter and creates projects and tasks in the Agent Workbench API for any
file whose status is "ready".

Usage:
  uv run scripts/onboard.py [--onboarding-dir DIR] [--api-url URL] [--dry-run]

Projects are processed before tasks in each run, so a project file and its
task files can be submitted together in a single batch.

--- type: project front matter ---
  type:          project                        (required)
  status:        draft | ready | processed      (required)
  name:          display name                   (required)
  slug:          unique URL-safe identifier     (required)
  project_type:  code | course | content | research | infrastructure | other
  local_path:    absolute path on disk
  git_remote_url: remote Git URL
  environment:   local | dev | stage | prod     (default: local)
  default_agent: default agent name

--- type: task front matter (type may be omitted; defaults to task) ---
  type:       task                              (optional, default)
  status:     draft | ready | processed        (required)
  title:      task title                        (required)
  project:    project slug                      (required)
  phase:      discovery | design | implementation | testing | review
  role:       researcher | planner | implementer | writer | reviewer | tester | orchestrator
  model_tier: cloud | local
  priority:   integer (default 5, higher = more urgent)

Files matching *.template.md are always ignored.
On success each file is rewritten with status: processed plus tracking fields
added to the front matter.
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


def api_create_project(api_url: str, fm: dict) -> dict:
    payload: dict = {
        "name": fm["name"],
        "slug": fm["slug"],
    }
    if fm.get("project_type"):
        payload["project_type"] = fm["project_type"]
    if fm.get("local_path"):
        payload["local_path"] = fm["local_path"]
    if fm.get("git_remote_url"):
        payload["git_remote_url"] = fm["git_remote_url"]
    if fm.get("environment"):
        payload["environment"] = fm["environment"]
    if fm.get("default_agent"):
        payload["default_agent"] = fm["default_agent"]

    resp = requests.post(f"{api_url}/api/projects", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def api_create_task(api_url: str, project_id: str, fm: dict, body: str) -> dict:
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


def process_project_file(path: Path, api_url: str, dry_run: bool) -> str:
    text = path.read_text()
    fm, body = parse_front_matter(text)

    status = fm.get("status", "draft")
    if status != "ready":
        return f"skip ({status})"

    name = str(fm.get("name", "")).strip()
    slug = str(fm.get("slug", "")).strip()

    if not name:
        return "error: missing required field 'name'"
    if not slug:
        return "error: missing required field 'slug'"

    if dry_run:
        project_type = fm.get("project_type", "code")
        return f"dry-run: would create project [{project_type}] '{name}' (slug: {slug})"

    try:
        project = api_create_project(api_url, fm)
    except requests.HTTPError as e:
        return f"error: API {e.response.status_code} — {e.response.text[:120]}"

    fm["status"] = "processed"
    fm["project_id"] = project["id"]
    fm["processed_at"] = datetime.now(timezone.utc).isoformat()
    write_front_matter(path, fm, body)

    return f"created project {project['id']}"


def process_task_file(path: Path, api_url: str, dry_run: bool) -> str:
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
        return f"dry-run: would create task [{phase}/{tier}] '{title}' → project '{project_slug}'"

    project_id = get_project_id(api_url, project_slug)
    if project_id is None:
        return f"error: project slug '{project_slug}' not found in API"

    try:
        task = api_create_task(api_url, project_id, fm, body)
    except requests.HTTPError as e:
        return f"error: API {e.response.status_code} — {e.response.text[:120]}"

    fm["status"] = "processed"
    fm["task_id"] = task["id"]
    fm["processed_at"] = datetime.now(timezone.utc).isoformat()
    write_front_matter(path, fm, body)

    return f"created task {task['id']}"


def archive_file(path: Path, archive_dir: Path, dry_run: bool) -> str:
    text = path.read_text()
    fm, _ = parse_front_matter(text)

    if fm.get("status") != "processed":
        return f"skip ({fm.get('status', 'draft')})"

    dest = archive_dir / path.name
    if dest.exists():
        # Avoid silent overwrite — append a counter suffix.
        stem, suffix = path.stem, path.suffix
        counter = 1
        while dest.exists():
            dest = archive_dir / f"{stem}.{counter}{suffix}"
            counter += 1

    if dry_run:
        return f"dry-run: would move → archive/{dest.name}"

    path.rename(dest)
    return f"archived → archive/{dest.name}"


def run_archive(onboarding_dir: Path, dry_run: bool) -> int:
    archive_dir = onboarding_dir / "archive"
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)

    files = sorted(
        f for f in onboarding_dir.glob("*.md")
        if not f.name.endswith(".template.md")
    )

    if not files:
        print("No onboarding files found.")
        return 0

    errors = 0
    for f in files:
        result = archive_file(f, archive_dir, dry_run)
        icon = "✗" if result.startswith("error") else "·"
        print(f"  {icon} {f.name}: {result}")
        if result.startswith("error"):
            errors += 1

    return errors


def process_file(path: Path, api_url: str, dry_run: bool) -> str:
    text = path.read_text()
    fm, _ = parse_front_matter(text)
    record_type = str(fm.get("type", "task")).strip().lower()

    if record_type == "project":
        return process_project_file(path, api_url, dry_run)
    elif record_type == "task":
        return process_task_file(path, api_url, dry_run)
    else:
        return f"error: unknown type '{record_type}'; must be 'project' or 'task'"


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard Markdown prompts as workbench projects and tasks")
    parser.add_argument("--onboarding-dir", default="onboarding", help="Directory to scan (default: onboarding/)")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Agent Workbench API URL")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating records or modifying files")
    parser.add_argument("--archive", action="store_true", help="Archive pass: move processed files to onboarding/archive/")
    args = parser.parse_args()

    onboarding_dir = Path(args.onboarding_dir)
    if not onboarding_dir.is_dir():
        print(f"error: onboarding directory not found: {onboarding_dir}", file=sys.stderr)
        sys.exit(1)

    if args.archive:
        errors = run_archive(onboarding_dir, args.dry_run)
        if errors:
            sys.exit(1)
        return

    api_url = args.api_url.rstrip("/")

    all_files = sorted(f for f in onboarding_dir.glob("*.md") if not f.name.endswith(".template.md"))

    if not all_files:
        print("No onboarding files found.")
        return

    # Partition into projects and tasks so projects are always registered first.
    project_files: list[Path] = []
    task_files: list[Path] = []
    unknown_files: list[Path] = []

    for f in all_files:
        text = f.read_text()
        fm, _ = parse_front_matter(text)
        record_type = str(fm.get("type", "task")).strip().lower()
        if record_type == "project":
            project_files.append(f)
        elif record_type == "task":
            task_files.append(f)
        else:
            unknown_files.append(f)

    errors = 0

    if project_files:
        print("Projects:")
        for f in project_files:
            result = process_file(f, api_url, args.dry_run)
            icon = "✗" if result.startswith("error") else "·"
            print(f"  {icon} {f.name}: {result}")
            if result.startswith("error"):
                errors += 1

    if task_files:
        print("Tasks:")
        for f in task_files:
            result = process_file(f, api_url, args.dry_run)
            icon = "✗" if result.startswith("error") else "·"
            print(f"  {icon} {f.name}: {result}")
            if result.startswith("error"):
                errors += 1

    for f in unknown_files:
        text = f.read_text()
        fm, _ = parse_front_matter(text)
        record_type = fm.get("type", "task")
        print(f"  ✗ {f.name}: error: unknown type '{record_type}'; must be 'project' or 'task'")
        errors += 1

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
