from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from ..projects import service as projects_service
from . import service
from .models import ProjectSection

bp = Blueprint("project_sections", __name__, url_prefix="/api/projects")


def _serialize(s: ProjectSection) -> dict:
    return {
        "id": str(s.id),
        "project_id": str(s.project_id),
        "name": s.name,
        "slug": s.slug,
        "section_type": s.section_type,
        "description": s.description,
        "sort_order": s.sort_order,
        "metadata": s.section_metadata,
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


@bp.get("/<project_id>/sections")
def list_sections(project_id: str):
    project = _resolve_project(project_id)

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        abort(400, "page and per_page must be integers")

    items, total = service.list_sections(project.id, page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify({
        "items": [_serialize(s) for s in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })


@bp.post("/<project_id>/sections")
def create_section(project_id: str):
    project = _resolve_project(project_id)

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    missing = [f for f in ("name", "slug") if not data.get(f)]
    if missing:
        abort(422, f"Missing required fields: {', '.join(missing)}")

    try:
        section = service.create_section(project.id, data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, f"A section with slug '{data['slug']}' already exists in this project")

    return jsonify(_serialize(section)), 201


@bp.get("/<project_id>/sections/<section_id>")
def get_section(project_id: str, section_id: str):
    project = _resolve_project(project_id)

    try:
        sid = uuid.UUID(section_id)
    except ValueError:
        abort(400, "section_id must be a valid UUID")

    section = service.get_section(sid)
    if section is None or section.project_id != project.id:
        abort(404, f"Section {section_id} not found")
    return jsonify(_serialize(section))


@bp.patch("/<project_id>/sections/<section_id>")
def update_section(project_id: str, section_id: str):
    project = _resolve_project(project_id)

    try:
        sid = uuid.UUID(section_id)
    except ValueError:
        abort(400, "section_id must be a valid UUID")

    section = service.get_section(sid)
    if section is None or section.project_id != project.id:
        abort(404, f"Section {section_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != section.version:
        abort(409, f"Version conflict: expected {section.version}, got {data['version']}")

    try:
        section = service.update_section(section, data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "A section with that slug already exists in this project")

    return jsonify(_serialize(section))
