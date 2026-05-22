from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request

from ..database import db
from ..projects import service as projects_service
from . import service
from .models import Event

bp = Blueprint("events", __name__, url_prefix="/api")


def _serialize(e: Event) -> dict:
    return {
        "id": str(e.id),
        "project_id": str(e.project_id) if e.project_id else None,
        "task_id": str(e.task_id) if e.task_id else None,
        "run_id": str(e.run_id) if e.run_id else None,
        "event_type": e.event_type,
        "actor_type": e.actor_type,
        "actor_name": e.actor_name,
        "payload": e.payload,
        "created_at": e.created_at.isoformat(),
    }


@bp.get("/projects/<project_id>/events")
def list_events(project_id: str):
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        abort(400, "project_id must be a valid UUID")

    if projects_service.get_project(pid) is None:
        abort(404, f"Project {project_id} not found")

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(200, max(1, int(request.args.get("per_page", 50))))
    except (ValueError, TypeError):
        abort(400, "page and per_page must be integers")

    items, total = service.list_events(pid, page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify({
        "items": [_serialize(e) for e in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })


@bp.post("/events")
def append_event():
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if not data.get("event_type"):
        abort(422, "Missing required field: event_type")

    for field in ("project_id", "task_id", "run_id"):
        val = data.get(field)
        if val:
            try:
                uuid.UUID(val)
            except ValueError:
                abort(400, f"{field} must be a valid UUID")

    event = service.append_event(data)
    db.session.commit()
    return jsonify(_serialize(event)), 201
