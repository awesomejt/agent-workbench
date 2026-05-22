from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request

from ..database import db
from ..projects import service as projects_service
from . import service
from .models import Review

bp = Blueprint("reviews", __name__, url_prefix="/api")


def _serialize(r: Review) -> dict:
    return {
        "id": str(r.id),
        "project_id": str(r.project_id),
        "source": r.source,
        "severity": r.severity,
        "status": r.status,
        "finding": r.finding,
        "recommendation": r.recommendation,
        "linked_task_id": str(r.linked_task_id) if r.linked_task_id else None,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
        "version": r.version,
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


@bp.get("/projects/<project_id>/reviews")
def list_reviews(project_id: str):
    project = _resolve_project(project_id)

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        abort(400, "page and per_page must be integers")

    items, total = service.list_reviews(project.id, page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify({
        "items": [_serialize(r) for r in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })


@bp.post("/projects/<project_id>/reviews")
def create_review(project_id: str):
    project = _resolve_project(project_id)

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if not data.get("finding"):
        abort(422, "Missing required field: finding")

    linked_task_id = data.get("linked_task_id")
    if linked_task_id:
        try:
            uuid.UUID(linked_task_id)
        except ValueError:
            abort(400, "linked_task_id must be a valid UUID")

    review = service.create_review(project.id, data)
    db.session.commit()
    return jsonify(_serialize(review)), 201


@bp.patch("/reviews/<review_id>")
def update_review(review_id: str):
    try:
        rid = uuid.UUID(review_id)
    except ValueError:
        abort(400, "review_id must be a valid UUID")

    review = service.get_review(rid)
    if review is None:
        abort(404, f"Review {review_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != review.version:
        abort(409, f"Version conflict: expected {review.version}, got {data['version']}")

    linked_task_id = data.get("linked_task_id")
    if linked_task_id:
        try:
            uuid.UUID(linked_task_id)
        except ValueError:
            abort(400, "linked_task_id must be a valid UUID")

    review = service.update_review(review, data)
    db.session.commit()
    return jsonify(_serialize(review))
