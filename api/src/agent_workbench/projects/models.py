from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import db


def _now() -> datetime:
    return datetime.now(UTC)


class Project(db.Model):  # type: ignore[name-defined]
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    project_type: Mapped[str] = mapped_column(String(64), nullable=False, default="development")
    git_remote_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(64), nullable=False, default="local")
    default_agent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    sections: Mapped[list] = relationship("ProjectSection", back_populates="project", lazy="select")
    tasks: Mapped[list] = relationship("Task", back_populates="project", lazy="select")
    runs: Mapped[list] = relationship("Run", back_populates="project", lazy="select")
    events: Mapped[list] = relationship("Event", back_populates="project", lazy="select")
    reviews: Mapped[list] = relationship("Review", back_populates="project", lazy="select")
