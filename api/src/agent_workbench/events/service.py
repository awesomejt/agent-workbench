from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import Event


def list_events(
    project_id: uuid.UUID, page: int = 1, per_page: int = 50
) -> tuple[list[Event], int]:
    per_page = min(per_page, 200)
    offset = (page - 1) * per_page
    base = select(Event).where(Event.project_id == project_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(
        base.order_by(Event.created_at.desc()).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def append_event(data: dict) -> Event:
    project_id = data.get("project_id")
    task_id = data.get("task_id")
    run_id = data.get("run_id")
    event = Event(
        project_id=uuid.UUID(project_id) if project_id else None,
        task_id=uuid.UUID(task_id) if task_id else None,
        run_id=uuid.UUID(run_id) if run_id else None,
        event_type=data["event_type"],
        actor_type=data.get("actor_type"),
        actor_name=data.get("actor_name"),
        payload=data.get("payload"),
    )
    db.session.add(event)
    db.session.flush()
    return event
