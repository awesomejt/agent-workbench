from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import Project


def list_projects(page: int = 1, per_page: int = 20) -> tuple[list[Project], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    total = db.session.scalar(select(func.count()).select_from(Project)) or 0
    items = db.session.scalars(
        select(Project).order_by(Project.created_at.desc()).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def get_project(project_id: uuid.UUID) -> Project | None:
    return db.session.get(Project, project_id)


def create_project(data: dict) -> Project:
    project = Project(
        name=data["name"],
        slug=data["slug"],
        project_type=data.get("project_type", "development"),
        git_remote_url=data.get("git_remote_url"),
        local_path=data.get("local_path"),
        environment=data.get("environment", "local"),
        default_agent=data.get("default_agent"),
        project_metadata=data.get("metadata"),
    )
    db.session.add(project)
    db.session.flush()
    return project


def update_project(project: Project, data: dict) -> Project:
    mutable = (
        "name",
        "project_type",
        "git_remote_url",
        "local_path",
        "environment",
        "default_agent",
        "slug",
    )
    for field in mutable:
        if field in data:
            setattr(project, field, data[field])
    if "metadata" in data:
        project.project_metadata = data["metadata"]
    project.version += 1
    db.session.flush()
    return project
