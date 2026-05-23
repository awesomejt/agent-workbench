from __future__ import annotations

import json
import math
import uuid

from flask import Blueprint, Response, abort, jsonify, make_response, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from ..idempotency import service as idempotency_service
from ..project_sections import service as sections_service
from ..projects import service as projects_service
from . import service
from .models import Task
from .service import DEFAULT_LEASE_SECONDS, LeaseConflictError, LeaseOwnershipError

_VALID_STATUSES = frozenset({"pending", "completed", "blocked"})
_VALID_PHASES = frozenset({"planning", "research", "implementation", "testing", "review"})
_VALID_STATUSES_STR = ", ".join(sorted(_VALID_STATUSES))
_VALID_PHASES_STR = ", ".join(sorted(_VALID_PHASES))
_MAX_DURATION_SECONDS = 7 * 24 * 3600  # 1 week hard cap

bp = Blueprint("tasks", __name__, url_prefix="/api")


def _serialize(t: Task) -> dict:
    return {
        "id": str(t.id),
        "project_id": str(t.project_id),
        "project_section_id": str(t.project_section_id) if t.project_section_id else None,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "phase": t.phase,
        "dependencies": t.dependencies,
        "assignee_type": t.assignee_type,
        "assignee_name": t.assignee_name,
        "estimated_duration_seconds": t.estimated_duration_seconds,
        "claimed_by": t.claimed_by,
        "claimed_until": t.claimed_until.isoformat() if t.claimed_until else None,
        "lease_version": t.lease_version,
        "validation_expectations": t.validation_expectations,
        "completion_evidence": t.completion_evidence,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "version": t.version,
    }


def _resolve_project(project_id: str):
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        abort(400, "project_id must be a valid UUID")
    project = projects_service.get_project(pid)
    if project is None:
        abort(404, f"Project {project_id} not found")
    return project


def _check_idempotency(endpoint: str, agent_name: str) -> tuple[str | None, Response | None]:
    """Return (key, cached_response) from the Idempotency-Key header.

    If a key is present and a cached response exists, the caller should return
    the Response immediately.  If no key, both values are None.
    """
    key = request.headers.get("Idempotency-Key")
    if not key:
        return None, None
    cached = idempotency_service.check_key(key, endpoint, agent_name)
    if cached is None:
        return key, None
    resp = make_response(cached["body"], cached["status"])
    resp.headers["Content-Type"] = "application/json"
    return key, resp


def _store_idempotency(
    key: str | None, endpoint: str, agent_name: str, body: dict, status: int
) -> None:
    if key:
        idempotency_service.store_key(key, endpoint, agent_name, status, json.dumps(body))


@bp.get("/projects/<project_id>/tasks")
def list_tasks(project_id: str):
    project = _resolve_project(project_id)

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError, TypeError:
        abort(400, "page and per_page must be integers")

    status_filter = request.args.get("status")
    phase_filter = request.args.get("phase")
    available = request.args.get("available", "").lower() in ("1", "true", "yes")

    items, total = service.list_tasks(
        project.id,
        page=page,
        per_page=per_page,
        status=status_filter,
        phase=phase_filter,
        available=available,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify(
        {
            "items": [_serialize(t) for t in items],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    )


@bp.post("/projects/<project_id>/tasks")
def create_task(project_id: str):
    project = _resolve_project(project_id)

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if not data.get("title"):
        abort(422, "Missing required field: title")

    if "status" in data and data["status"] not in _VALID_STATUSES:
        abort(422, f"Invalid status '{data['status']}'; valid: {_VALID_STATUSES_STR}")

    if "phase" in data and data["phase"] not in _VALID_PHASES:
        abort(422, f"Invalid phase '{data['phase']}'; valid: {_VALID_PHASES_STR}")

    section_id = data.get("project_section_id")
    if section_id:
        try:
            sid = uuid.UUID(section_id)
        except ValueError:
            abort(400, "project_section_id must be a valid UUID")
        section = sections_service.get_section(sid)
        if section is None or section.project_id != project.id:
            abort(422, "project_section_id does not belong to this project")

    task = service.create_task(project.id, data)
    db.session.commit()
    return jsonify(_serialize(task)), 201


@bp.get("/tasks/<task_id>")
def get_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    task = service.get_task(tid)
    if task is None:
        abort(404, f"Task {task_id} not found")
    return jsonify(_serialize(task))


@bp.patch("/tasks/<task_id>")
def update_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    task = service.get_task(tid)
    if task is None:
        abort(404, f"Task {task_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != task.version:
        abort(409, f"Version conflict: expected {task.version}, got {data['version']}")

    if "status" in data and data["status"] not in _VALID_STATUSES:
        abort(422, f"Invalid status '{data['status']}'; valid: {_VALID_STATUSES_STR}")

    if "phase" in data and data["phase"] not in _VALID_PHASES:
        abort(422, f"Invalid phase '{data['phase']}'; valid: {_VALID_PHASES_STR}")

    if "project_section_id" in data and data["project_section_id"] is not None:
        try:
            sid = uuid.UUID(data["project_section_id"])
        except ValueError:
            abort(400, "project_section_id must be a valid UUID")
        section = sections_service.get_section(sid)
        if section is None or section.project_id != task.project_id:
            abort(422, "project_section_id does not belong to this project")

    task = service.update_task(task, data)
    db.session.commit()
    return jsonify(_serialize(task))


@bp.post("/tasks/<task_id>/claim")
def claim_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent_name")
    if not agent_name:
        abort(422, "agent_name is required")

    idem_key, cached_resp = _check_idempotency("task.claim", agent_name)
    if cached_resp is not None:
        return cached_resp

    # Duration priority: request body > task's per-task estimate > system default
    task_obj = service.get_task(tid)
    if task_obj is None:
        abort(404, f"Task {task_id} not found")
    if "duration_seconds" in data:
        try:
            req_duration = int(data["duration_seconds"])
        except TypeError, ValueError:
            abort(422, "duration_seconds must be a positive integer")
        if req_duration <= 0 or req_duration > _MAX_DURATION_SECONDS:
            abort(422, f"duration_seconds must be between 1 and {_MAX_DURATION_SECONDS}")
        duration = req_duration
    else:
        duration = task_obj.estimated_duration_seconds or DEFAULT_LEASE_SECONDS

    try:
        task = service.claim_task(tid, agent_name, duration=duration)
        response_body = _serialize(task)
        _store_idempotency(idem_key, "task.claim", agent_name, response_body, 200)
        db.session.commit()
    except LeaseConflictError as e:
        db.session.rollback()
        abort(409, str(e))
    except IntegrityError:
        db.session.rollback()
        abort(409, "Duplicate idempotency key")

    return jsonify(response_body)


@bp.post("/tasks/<task_id>/heartbeat")
def heartbeat_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent_name")
    if not agent_name:
        abort(422, "agent_name is required")

    idem_key, cached_resp = _check_idempotency("task.heartbeat", agent_name)
    if cached_resp is not None:
        return cached_resp

    task_obj = service.get_task(tid)
    if task_obj is None:
        abort(404, f"Task {task_id} not found")
    if "duration_seconds" in data:
        try:
            req_duration = int(data["duration_seconds"])
        except TypeError, ValueError:
            abort(422, "duration_seconds must be a positive integer")
        if req_duration <= 0 or req_duration > _MAX_DURATION_SECONDS:
            abort(422, f"duration_seconds must be between 1 and {_MAX_DURATION_SECONDS}")
        duration = req_duration
    else:
        duration = task_obj.estimated_duration_seconds or DEFAULT_LEASE_SECONDS

    try:
        task = service.heartbeat_task(tid, agent_name, duration=duration)
        response_body = _serialize(task)
        _store_idempotency(idem_key, "task.heartbeat", agent_name, response_body, 200)
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(response_body)


@bp.post("/tasks/<task_id>/complete")
def complete_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    if service.get_task(tid) is None:
        abort(404, f"Task {task_id} not found")

    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent_name")
    if not agent_name:
        abort(422, "agent_name is required")

    idem_key, cached_resp = _check_idempotency("task.complete", agent_name)
    if cached_resp is not None:
        return cached_resp

    try:
        task = service.complete_task(tid, agent_name, evidence=data.get("evidence"))
        response_body = _serialize(task)
        _store_idempotency(idem_key, "task.complete", agent_name, response_body, 200)
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(response_body)


@bp.post("/tasks/<task_id>/block")
def block_task(task_id: str):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        abort(400, "task_id must be a valid UUID")

    if service.get_task(tid) is None:
        abort(404, f"Task {task_id} not found")

    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent_name")
    if not agent_name:
        abort(422, "agent_name is required")

    idem_key, cached_resp = _check_idempotency("task.block", agent_name)
    if cached_resp is not None:
        return cached_resp

    try:
        task = service.block_task(tid, agent_name, reason=data.get("reason"))
        response_body = _serialize(task)
        _store_idempotency(idem_key, "task.block", agent_name, response_body, 200)
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(response_body)
