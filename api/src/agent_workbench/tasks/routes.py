from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from ..projects import service as projects_service
from . import service
from .models import Task
from .service import DEFAULT_LEASE_SECONDS, LeaseConflictError, LeaseOwnershipError

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


@bp.get("/projects/<project_id>/tasks")
def list_tasks(project_id: str):
    project = _resolve_project(project_id)

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        abort(400, "page and per_page must be integers")

    status_filter = request.args.get("status")
    phase_filter = request.args.get("phase")

    items, total = service.list_tasks(
        project.id, page=page, per_page=per_page,
        status=status_filter, phase=phase_filter,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify({
        "items": [_serialize(t) for t in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })


@bp.post("/projects/<project_id>/tasks")
def create_task(project_id: str):
    project = _resolve_project(project_id)

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if not data.get("title"):
        abort(422, "Missing required field: title")

    section_id = data.get("project_section_id")
    if section_id:
        try:
            uuid.UUID(section_id)
        except ValueError:
            abort(400, "project_section_id must be a valid UUID")

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

    # Duration priority: request body > task's per-task estimate > system default
    task_obj = service.get_task(tid)
    if task_obj is None:
        abort(404, f"Task {task_id} not found")
    duration = int(
        data["duration_seconds"]
        if "duration_seconds" in data
        else (task_obj.estimated_duration_seconds or DEFAULT_LEASE_SECONDS)
    )
    idempotency_key = data.get("idempotency_key")

    try:
        task = service.claim_task(
            tid, agent_name, duration=duration, idempotency_key=idempotency_key
        )
        db.session.commit()
    except LeaseConflictError as e:
        db.session.rollback()
        abort(409, str(e))
    except IntegrityError:
        db.session.rollback()
        abort(409, "Duplicate idempotency key")

    return jsonify(_serialize(task))


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

    task_obj = service.get_task(tid)
    if task_obj is None:
        abort(404, f"Task {task_id} not found")
    duration = int(
        data["duration_seconds"]
        if "duration_seconds" in data
        else (task_obj.estimated_duration_seconds or DEFAULT_LEASE_SECONDS)
    )

    try:
        task = service.heartbeat_task(tid, agent_name, duration=duration)
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(task))


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

    try:
        task = service.complete_task(tid, agent_name, evidence=data.get("evidence"))
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(task))


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

    try:
        task = service.block_task(tid, agent_name, reason=data.get("reason"))
        db.session.commit()
    except LeaseOwnershipError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(task))
