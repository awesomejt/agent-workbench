from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request

from ..database import db
from ..projects import service as projects_service
from . import service
from .models import ProjectStatus

bp = Blueprint("project_status", __name__, url_prefix="/api/projects")


def _serialize(s: ProjectStatus) -> dict:
    return {
        "id": str(s.id),
        "project_id": str(s.project_id),
        "project_section_id": str(s.project_section_id) if s.project_section_id else None,
        "status": s.status,
        "phase": s.phase,
        "summary": s.summary,
        "reason": s.reason,
        "details": s.details,
        "source": s.source,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
        "version": s.version,
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


@bp.get("/<project_id>/status")
def list_statuses(project_id: str):
    project = _resolve_project(project_id)

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        abort(400, "page and per_page must be integers")

    items, total = service.list_statuses(project.id, page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify({
        "items": [_serialize(s) for s in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })


@bp.post("/<project_id>/status")
def create_status(project_id: str):
    project = _resolve_project(project_id)

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    section_id = data.get("project_section_id")
    if section_id:
        try:
            uuid.UUID(section_id)
        except ValueError:
            abort(400, "project_section_id must be a valid UUID")

    status = service.create_status(project.id, data)
    db.session.commit()
    return jsonify(_serialize(status)), 201


@bp.patch("/<project_id>/status/<status_id>")
def update_status(project_id: str, status_id: str):
    project = _resolve_project(project_id)

    try:
        sid = uuid.UUID(status_id)
    except ValueError:
        abort(400, "status_id must be a valid UUID")

    status = service.get_status(sid)
    if status is None or status.project_id != project.id:
        abort(404, f"Status {status_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != status.version:
        abort(409, f"Version conflict: expected {status.version}, got {data['version']}")

    status = service.update_status(status, data)
    db.session.commit()
    return jsonify(_serialize(status))
