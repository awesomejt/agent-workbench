from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import SCHEMA, db

if TYPE_CHECKING:
    from ..projects.models import Project


def _now() -> datetime:
    return datetime.now(UTC)


class Task(db.Model):  # type: ignore[name-defined]
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{SCHEMA}.projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_section_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{SCHEMA}.project_sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    phase: Mapped[str] = mapped_column(String(64), nullable=False, default="planning")
    dependencies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    assignee_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assignee_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Lease fields for atomic task claiming
    claimed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    claimed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Per-task lease window in seconds; overrides the system default when set.
    # Set this generously for local AI agents — token generation can take many minutes.
    estimated_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_expectations: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    project: Mapped[Project] = relationship("Project", back_populates="tasks")
    runs: Mapped[list] = relationship("Run", back_populates="task", lazy="select")
    events: Mapped[list] = relationship("Event", back_populates="task", lazy="select")
    outgoing_relationships: Mapped[list] = relationship(
        "TaskRelationship",
        foreign_keys="[TaskRelationship.from_task_id]",
        back_populates="from_task",
        lazy="select",
    )
    incoming_relationships: Mapped[list] = relationship(
        "TaskRelationship",
        foreign_keys="[TaskRelationship.to_task_id]",
        back_populates="to_task",
        lazy="select",
    )


class TaskRelationship(db.Model):  # type: ignore[name-defined]
    __tablename__ = "task_relationships"
    __table_args__ = (
        UniqueConstraint(
            "from_task_id", "to_task_id", "relationship_type", name="uq_task_rel_from_to_type"
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{SCHEMA}.tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{SCHEMA}.tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    from_task: Mapped[Task] = relationship(
        "Task", foreign_keys=[from_task_id], back_populates="outgoing_relationships"
    )
    to_task: Mapped[Task] = relationship(
        "Task", foreign_keys=[to_task_id], back_populates="incoming_relationships"
    )
