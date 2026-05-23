from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import Agent


def list_agents(page: int = 1, per_page: int = 20) -> tuple[list[Agent], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    total = db.session.scalar(select(func.count()).select_from(Agent)) or 0
    items = db.session.scalars(
        select(Agent).order_by(Agent.name).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def get_agent(agent_id: uuid.UUID) -> Agent | None:
    return db.session.get(Agent, agent_id)


def create_agent(data: dict) -> Agent:
    agent = Agent(
        name=data["name"],
        agent_type=data.get("agent_type", "local"),
        capabilities=data.get("capabilities"),
        default_model=data.get("default_model"),
        model_tier=data.get("model_tier"),
        runtime_notes=data.get("runtime_notes"),
    )
    db.session.add(agent)
    db.session.flush()
    return agent


def update_agent(agent: Agent, data: dict) -> Agent:
    mutable = ("name", "agent_type", "capabilities", "default_model", "model_tier", "runtime_notes")
    for field in mutable:
        if field in data:
            setattr(agent, field, data[field])
    agent.version += 1
    db.session.flush()
    return agent
