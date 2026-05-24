from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from . import service
from .models import AiServer

_VALID_SERVER_TYPES = frozenset({"ollama", "litellm", "omlx", "openai_compat"})
_VALID_STATUSES = frozenset({"up", "down", "unknown"})
_VALID_SERVER_TYPES_STR = ", ".join(sorted(_VALID_SERVER_TYPES))
_VALID_STATUSES_STR = ", ".join(sorted(_VALID_STATUSES))

bp = Blueprint("ai_servers", __name__, url_prefix="/api/ai-servers")


def _serialize(s: AiServer) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "url": s.url,
        "server_type": s.server_type,
        "status": s.status,
        "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
        "last_up_at": s.last_up_at.isoformat() if s.last_up_at else None,
        "last_error": s.last_error,
        "notes": s.notes,
        "metadata": s.server_metadata,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
        "version": s.version,
    }


@bp.get("")
def list_servers():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        abort(400, "page and per_page must be integers")

    status_filter = request.args.get("status")
    available = request.args.get("available", "").lower() in ("1", "true")

    if status_filter and status_filter not in _VALID_STATUSES:
        abort(422, f"Invalid status '{status_filter}'; valid: {_VALID_STATUSES_STR}")

    items, total = service.list_servers(
        page=page, per_page=per_page, status=status_filter, available=available
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify(
        {
            "items": [_serialize(s) for s in items],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    )


@bp.post("")
def create_server():
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    missing = [f for f in ("name", "url", "server_type") if not data.get(f)]
    if missing:
        abort(422, f"Missing required fields: {', '.join(missing)}")

    if data["server_type"] not in _VALID_SERVER_TYPES:
        abort(
            422,
            f"Invalid server_type '{data['server_type']}'; valid: {_VALID_SERVER_TYPES_STR}",
        )

    try:
        server = service.create_server(data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, f"A server named '{data['name']}' already exists")

    return jsonify(_serialize(server)), 201


@bp.get("/<server_id>")
def get_server(server_id: str):
    try:
        sid = uuid.UUID(server_id)
    except ValueError:
        abort(400, "server_id must be a valid UUID")

    server = service.get_server(sid)
    if server is None:
        abort(404, f"AI server {server_id} not found")
    return jsonify(_serialize(server))


@bp.patch("/<server_id>")
def update_server(server_id: str):
    try:
        sid = uuid.UUID(server_id)
    except ValueError:
        abort(400, "server_id must be a valid UUID")

    server = service.get_server(sid)
    if server is None:
        abort(404, f"AI server {server_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != server.version:
        abort(409, f"Version conflict: expected {server.version}, got {data['version']}")

    if "server_type" in data and data["server_type"] not in _VALID_SERVER_TYPES:
        abort(
            422,
            f"Invalid server_type '{data['server_type']}'; valid: {_VALID_SERVER_TYPES_STR}",
        )

    if "status" in data and data["status"] not in _VALID_STATUSES:
        abort(422, f"Invalid status '{data['status']}'; valid: {_VALID_STATUSES_STR}")

    try:
        server = service.update_server(server, data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "A server with that name already exists")

    return jsonify(_serialize(server))


@bp.delete("/<server_id>")
def delete_server(server_id: str):
    try:
        sid = uuid.UUID(server_id)
    except ValueError:
        abort(400, "server_id must be a valid UUID")

    server = service.get_server(sid)
    if server is None:
        abort(404, f"AI server {server_id} not found")

    service.delete_server(server)
    db.session.commit()
    return "", 204
