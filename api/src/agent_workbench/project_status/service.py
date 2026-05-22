from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import ProjectStatus


def list_statuses(
    project_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[ProjectStatus], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(ProjectStatus).where(ProjectStatus.project_id == project_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(
        base.order_by(ProjectStatus.created_at.desc()).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def get_status(status_id: uuid.UUID) -> ProjectStatus | None:
    return db.session.get(ProjectStatus, status_id)


def create_status(project_id: uuid.UUID, data: dict) -> ProjectStatus:
    section_id = data.get("project_section_id")
    status = ProjectStatus(
        project_id=project_id,
        project_section_id=uuid.UUID(section_id) if section_id else None,
        status=data.get("status", "active"),
        phase=data.get("phase", "planning"),
        summary=data.get("summary"),
        reason=data.get("reason"),
        details=data.get("details"),
        source=data.get("source"),
    )
    db.session.add(status)
    db.session.flush()
    return status


def update_status(status: ProjectStatus, data: dict) -> ProjectStatus:
    mutable = ("status", "phase", "summary", "reason", "details", "source")
    for field in mutable:
        if field in data:
            setattr(status, field, data[field])
    if "project_section_id" in data:
        sid = data["project_section_id"]
        status.project_section_id = uuid.UUID(sid) if sid else None
    status.version += 1
    db.session.flush()
    return status
