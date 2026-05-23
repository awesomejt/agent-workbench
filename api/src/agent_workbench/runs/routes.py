from __future__ import annotations

import uuid

from flask import Blueprint, abort, jsonify, request

from ..database import db
from ..projects import service as projects_service
from ..tasks import service as tasks_service
from . import service
from .models import Run
from .service import RunStateError

bp = Blueprint("runs", __name__, url_prefix="/api/runs")


def _serialize(r: Run) -> dict:
    return {
        "id": str(r.id),
        "project_id": str(r.project_id),
        "task_id": str(r.task_id) if r.task_id else None,
        "agent_name": r.agent_name,
        "status": r.status,
        "started_at": r.started_at.isoformat(),
        "last_heartbeat_at": r.last_heartbeat_at.isoformat() if r.last_heartbeat_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "validation_commands": r.validation_commands,
        "validation_result": r.validation_result,
        "summary": r.summary,
        "model_id": r.model_id,
        "prompt_tokens": r.prompt_tokens,
        "completion_tokens": r.completion_tokens,
        "latency_ms": r.latency_ms,
        "prompt_category": r.prompt_category,
        "version": r.version,
    }


@bp.post("")
def create_run():
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    missing = [f for f in ("project_id", "agent_name") if not data.get(f)]
    if missing:
        abort(422, f"Missing required fields: {', '.join(missing)}")

    try:
        project_uuid = uuid.UUID(data["project_id"])
    except ValueError:
        abort(400, "project_id must be a valid UUID")

    if projects_service.get_project(project_uuid) is None:
        abort(422, f"Project {data['project_id']} not found")

    task_id = data.get("task_id")
    if task_id:
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            abort(400, "task_id must be a valid UUID")
        task = tasks_service.get_task(task_uuid)
        if task is None or task.project_id != project_uuid:
            abort(422, "task_id does not belong to the provided project")

    run = service.create_run(data)
    db.session.commit()
    return jsonify(_serialize(run)), 201


@bp.get("/<run_id>")
def get_run(run_id: str):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        abort(400, "run_id must be a valid UUID")

    run = service.get_run(rid)
    if run is None:
        abort(404, f"Run {run_id} not found")
    return jsonify(_serialize(run))


@bp.post("/<run_id>/heartbeat")
def heartbeat_run(run_id: str):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        abort(400, "run_id must be a valid UUID")

    if service.get_run(rid) is None:
        abort(404, f"Run {run_id} not found")

    try:
        run = service.heartbeat_run(rid)
        db.session.commit()
    except RunStateError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(run))


@bp.post("/<run_id>/complete")
def complete_run(run_id: str):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        abort(400, "run_id must be a valid UUID")

    if service.get_run(rid) is None:
        abort(404, f"Run {run_id} not found")

    data = request.get_json(silent=True) or {}

    try:
        run = service.complete_run(rid, data)
        db.session.commit()
    except RunStateError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(run))


@bp.post("/<run_id>/fail")
def fail_run(run_id: str):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        abort(400, "run_id must be a valid UUID")

    if service.get_run(rid) is None:
        abort(404, f"Run {run_id} not found")

    data = request.get_json(silent=True) or {}

    try:
        run = service.fail_run(rid, data)
        db.session.commit()
    except RunStateError as e:
        db.session.rollback()
        abort(409, str(e))

    return jsonify(_serialize(run))
