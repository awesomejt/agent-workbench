from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import ProjectSection


def list_sections(
    project_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[ProjectSection], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(ProjectSection).where(ProjectSection.project_id == project_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(
        base.order_by(ProjectSection.sort_order, ProjectSection.created_at)
        .offset(offset)
        .limit(per_page)
    ).all()
    return list(items), total


def get_section(section_id: uuid.UUID) -> ProjectSection | None:
    return db.session.get(ProjectSection, section_id)


def create_section(project_id: uuid.UUID, data: dict) -> ProjectSection:
    section = ProjectSection(
        project_id=project_id,
        name=data["name"],
        slug=data["slug"],
        section_type=data.get("section_type", "module"),
        description=data.get("description"),
        sort_order=data.get("sort_order", 0),
        section_metadata=data.get("metadata"),
    )
    db.session.add(section)
    db.session.flush()
    return section


def update_section(section: ProjectSection, data: dict) -> ProjectSection:
    mutable = ("name", "slug", "section_type", "description", "sort_order")
    for field in mutable:
        if field in data:
            setattr(section, field, data[field])
    if "metadata" in data:
        section.section_metadata = data["metadata"]
    section.version += 1
    db.session.flush()
    return section
