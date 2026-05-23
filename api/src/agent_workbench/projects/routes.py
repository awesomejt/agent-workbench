from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from . import service
from .models import Project

_VALID_PROJECT_TYPES = frozenset(
    {"code", "course", "content", "research", "infrastructure", "other"}
)
_VALID_PROJECT_TYPES_STR = ", ".join(sorted(_VALID_PROJECT_TYPES))

bp = Blueprint("projects", __name__, url_prefix="/api/projects")


def _serialize(p: Project) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "slug": p.slug,
        "project_type": p.project_type,
        "git_remote_url": p.git_remote_url,
        "local_path": p.local_path,
        "environment": p.environment,
        "default_agent": p.default_agent,
        "metadata": p.project_metadata,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "version": p.version,
    }


@bp.get("")
def list_projects():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError, TypeError:
        abort(400, "page and per_page must be integers")

    items, total = service.list_projects(page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify(
        {
            "items": [_serialize(p) for p in items],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    )


@bp.post("")
def create_project():
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    missing = [f for f in ("name", "slug") if not data.get(f)]
    if missing:
        abort(422, f"Missing required fields: {', '.join(missing)}")

    if "project_type" in data and data["project_type"] not in _VALID_PROJECT_TYPES:
        abort(
            422,
            f"Invalid project_type '{data['project_type']}'; valid: {_VALID_PROJECT_TYPES_STR}",
        )

    try:
        project = service.create_project(data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, f"A project with slug '{data['slug']}' already exists")

    return jsonify(_serialize(project)), 201


@bp.get("/<project_id>")
def get_project(project_id: str):
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        abort(400, "project_id must be a valid UUID")

    project = service.get_project(pid)
    if project is None:
        abort(404, f"Project {project_id} not found")
    return jsonify(_serialize(project))


@bp.patch("/<project_id>")
def update_project(project_id: str):
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        abort(400, "project_id must be a valid UUID")

    project = service.get_project(pid)
    if project is None:
        abort(404, f"Project {project_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != project.version:
        abort(409, f"Version conflict: expected {project.version}, got {data['version']}")

    if "project_type" in data and data["project_type"] not in _VALID_PROJECT_TYPES:
        abort(
            422,
            f"Invalid project_type '{data['project_type']}'; valid: {_VALID_PROJECT_TYPES_STR}",
        )

    try:
        project = service.update_project(project, data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "A project with that slug already exists")

    return jsonify(_serialize(project))
