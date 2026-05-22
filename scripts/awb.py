#!/usr/bin/env python3
"""Bootstrap Agent Workbench CLI stub.

This is intentionally lightweight and local-state backed. It gives OpenCode a
stable command interface before the real database/API/Go CLI exists.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TODO_PATH = ROOT / "TODO.md"
STATUS_PATH = ROOT / "status.yaml"
STATE_DIR = ROOT / ".agent-workbench"
STATE_PATH = Path(os.environ.get("AGENT_WORKBENCH_BOOTSTRAP_STATE", STATE_DIR / "bootstrap-state.json"))

SKIP_SECTIONS = {
    "Needs Attention",
    "Manual Validation",
    "Review",
    "In Progress",
    "Blocked",
    "Done",
}

TASK_RE = re.compile(r"^\s*- \[ \] (?P<title>.+?)\s*$")
HEADING_RE = re.compile(r"^(?P<level>#{2,4})\s+(?P<title>.+?)\s*$")


@dataclass
class TodoTask:
    id: str
    title: str
    section: str
    line: int


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"claims": {}, "events": []}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def parse_todo_tasks() -> list[TodoTask]:
    if not TODO_PATH.exists():
        raise SystemExit("TODO.md not found")

    tasks: list[TodoTask] = []
    current_h2 = ""
    current_section = ""

    for idx, line in enumerate(TODO_PATH.read_text().splitlines(), start=1):
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group("title").strip()
            if heading.group("level") == "##":
                current_h2 = title
                current_section = title
            else:
                current_section = title
            continue

        match = TASK_RE.match(line)
        if not match:
            continue
        if current_h2 != "AI Agent Work":
            continue
        if current_section in SKIP_SECTIONS:
            continue

        title = match.group("title").strip()
        tasks.append(TodoTask(id=f"todo:L{idx}", title=title, section=current_section, line=idx))

    return tasks


def output(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, sort_keys=True)}")
            else:
                print(f"{key}: {value}")
    else:
        print(data)


def cmd_task_next(args: argparse.Namespace) -> int:
    state = load_state()
    claimed = state.get("claims", {})
    tasks = [task for task in parse_todo_tasks() if task.id not in claimed or claimed[task.id].get("status") in {"completed", "blocked"}]

    if not tasks:
        output({"status": "empty", "message": "No unclaimed AI Agent Work tasks found"}, args.json)
        return 1

    task = tasks[0]
    data = asdict(task) | {"status": "ready"}
    output(data, args.json)
    return 0


def cmd_task_claim(args: argparse.Namespace) -> int:
    state = load_state()
    task_id = args.task_id
    agent = args.agent
    claims = state.setdefault("claims", {})

    claims[task_id] = {
        "task_id": task_id,
        "agent": agent,
        "status": "claimed",
        "claimed_at": now_iso(),
        "last_heartbeat_at": now_iso(),
        "note": args.note,
    }
    state.setdefault("events", []).append({"at": now_iso(), "event": "task_claimed", "task_id": task_id, "agent": agent})
    save_state(state)
    output(claims[task_id], args.json)
    return 0


def cmd_task_heartbeat(args: argparse.Namespace) -> int:
    state = load_state()
    claim = state.setdefault("claims", {}).get(args.task_id)
    if not claim:
        raise SystemExit(f"Task is not claimed in bootstrap state: {args.task_id}")

    claim["last_heartbeat_at"] = now_iso()
    claim["status"] = "claimed"
    
    note = getattr(args, "note", "")
    summary = getattr(args, "summary", "")
    final_note = summary if summary else note
    
    if final_note:
        claim["note"] = final_note
    state.setdefault("events", []).append({"at": now_iso(), "event": "task_heartbeat", "task_id": args.task_id, "note": final_note})
    save_state(state)
    output(claim, args.json)
    return 0


def set_terminal_status(args: argparse.Namespace, status: str, event: str) -> int:
    state = load_state()
    claim = state.setdefault("claims", {}).setdefault(args.task_id, {"task_id": args.task_id})
    claim["status"] = status
    claim["finished_at"] = now_iso()
    
    note = getattr(args, "note", "")
    summary = getattr(args, "summary", "")
    final_note = summary if summary else note
    claim["note"] = final_note
    
    agent = getattr(args, "agent", "opencode")
    if agent:
        claim["agent"] = agent
        
    state.setdefault("events", []).append({
        "at": now_iso(), 
        "event": event, 
        "task_id": args.task_id, 
        "note": final_note,
        "agent": agent
    })
    save_state(state)
    output(claim, args.json)
    return 0


def cmd_status_show(args: argparse.Namespace) -> int:
    state = load_state()
    ready_count = len(parse_todo_tasks())
    data = {
        "repo": str(ROOT),
        "todo_path": str(TODO_PATH),
        "status_path": str(STATUS_PATH),
        "state_path": str(STATE_PATH),
        "ready_ai_agent_tasks": ready_count,
        "claims": state.get("claims", {}),
        "event_count": len(state.get("events", [])),
    }
    output(data, args.json)
    return 0


def add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit JSON output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent Workbench bootstrap command stub")
    add_json_flag(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    task_next = sub.add_parser("task-next", help="show the next unclaimed TODO task")
    add_json_flag(task_next)
    task_next.set_defaults(func=cmd_task_next)

    claim = sub.add_parser("task-claim", help="claim a task in local bootstrap state")
    add_json_flag(claim)
    claim.add_argument("task_id")
    claim.add_argument("--agent", default="opencode")
    claim.add_argument("--note", default="")
    claim.set_defaults(func=cmd_task_claim)

    heartbeat = sub.add_parser("task-heartbeat", help="heartbeat a claimed task")
    add_json_flag(heartbeat)
    heartbeat.add_argument("task_id")
    heartbeat.add_argument("--note", default="")
    heartbeat.add_argument("--summary", default="")
    heartbeat.add_argument("--agent", default="opencode")
    heartbeat.set_defaults(func=cmd_task_heartbeat)

    complete = sub.add_parser("task-complete", help="mark a task complete in local bootstrap state")
    add_json_flag(complete)
    complete.add_argument("task_id")
    complete.add_argument("--note", default="")
    complete.add_argument("--summary", default="")
    complete.add_argument("--agent", default="opencode")
    complete.set_defaults(func=lambda args: set_terminal_status(args, "completed", "task_completed"))

    block = sub.add_parser("task-block", help="mark a task blocked in local bootstrap state")
    add_json_flag(block)
    block.add_argument("task_id")
    block.add_argument("--note", default="")
    block.add_argument("--summary", default="")
    block.add_argument("--agent", default="opencode")
    block.set_defaults(func=lambda args: set_terminal_status(args, "blocked", "task_blocked"))

    status = sub.add_parser("status-show", help="show bootstrap state")
    add_json_flag(status)
    status.set_defaults(func=cmd_status_show)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except BrokenPipeError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
