from __future__ import annotations

import math
import uuid

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..database import db
from . import service
from .models import Agent

_VALID_MODEL_TIERS = frozenset({"local", "cloud"})
_VALID_MODEL_TIERS_STR = ", ".join(sorted(_VALID_MODEL_TIERS))

bp = Blueprint("agents", __name__, url_prefix="/api/agents")


def _serialize(a: Agent) -> dict:
    return {
        "id": str(a.id),
        "name": a.name,
        "agent_type": a.agent_type,
        "capabilities": a.capabilities,
        "default_model": a.default_model,
        "model_tier": a.model_tier,
        "runtime_notes": a.runtime_notes,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
        "version": a.version,
    }


@bp.get("")
def list_agents():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError, TypeError:
        abort(400, "page and per_page must be integers")

    items, total = service.list_agents(page=page, per_page=per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    return jsonify(
        {
            "items": [_serialize(a) for a in items],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    )


@bp.post("")
def create_agent():
    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if not data.get("name"):
        abort(422, "Missing required field: name")

    if "model_tier" in data and data["model_tier"] is not None:
        if data["model_tier"] not in _VALID_MODEL_TIERS:
            abort(
                422,
                f"Invalid model_tier '{data['model_tier']}'; valid: {_VALID_MODEL_TIERS_STR}",
            )

    try:
        agent = service.create_agent(data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, f"An agent named '{data['name']}' already exists")

    return jsonify(_serialize(agent)), 201


@bp.get("/<agent_id>")
def get_agent(agent_id: str):
    try:
        aid = uuid.UUID(agent_id)
    except ValueError:
        abort(400, "agent_id must be a valid UUID")

    agent = service.get_agent(aid)
    if agent is None:
        abort(404, f"Agent {agent_id} not found")
    return jsonify(_serialize(agent))


@bp.patch("/<agent_id>")
def update_agent(agent_id: str):
    try:
        aid = uuid.UUID(agent_id)
    except ValueError:
        abort(400, "agent_id must be a valid UUID")

    agent = service.get_agent(aid)
    if agent is None:
        abort(404, f"Agent {agent_id} not found")

    data = request.get_json(silent=True)
    if not data:
        abort(400, "Request body must be JSON")

    if "version" not in data:
        abort(422, "version is required for updates")

    if data["version"] != agent.version:
        abort(409, f"Version conflict: expected {agent.version}, got {data['version']}")

    if "model_tier" in data and data["model_tier"] is not None:
        if data["model_tier"] not in _VALID_MODEL_TIERS:
            abort(
                422,
                f"Invalid model_tier '{data['model_tier']}'; valid: {_VALID_MODEL_TIERS_STR}",
            )

    try:
        agent = service.update_agent(agent, data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "An agent with that name already exists")

    return jsonify(_serialize(agent))
