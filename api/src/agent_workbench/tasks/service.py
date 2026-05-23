from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, or_, select, update

from ..database import db
from ..events import service as events_service
from ..project_status import service as project_status_service
from .models import Task, TaskRelationship

DEFAULT_LEASE_SECONDS = 1800  # 30 minutes — generous default for local AI agents


class LeaseConflictError(Exception):
    pass


class LeaseOwnershipError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


def list_tasks(
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    phase: str | None = None,
    available: bool = False,
) -> tuple[list[Task], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(Task).where(Task.project_id == project_id)
    if status:
        base = base.where(Task.status == status)
    if phase:
        base = base.where(Task.phase == phase)
    if available:
        # "available" = pending (unclaimed or expired lease) OR in_progress with expired lease
        now = datetime.now(UTC)
        base = base.where(
            or_(
                and_(
                    Task.status == "pending",
                    or_(Task.claimed_until.is_(None), Task.claimed_until < now),
                ),
                and_(Task.status == "in_progress", Task.claimed_until < now),
            )
        )
        # Exclude tasks that have any incomplete 'blocks' predecessor
        blocking_ids = (
            select(TaskRelationship.to_task_id)
            .join(Task, Task.id == TaskRelationship.from_task_id)
            .where(TaskRelationship.relationship_type == "blocks")
            .where(Task.status != "completed")
            .scalar_subquery()
        )
        base = base.where(Task.id.notin_(blocking_ids))
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(
        base.order_by(Task.priority.desc(), Task.created_at).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def get_task(task_id: uuid.UUID) -> Task | None:
    return db.session.get(Task, task_id)


def create_task(project_id: uuid.UUID, data: dict) -> Task:
    section_id = data.get("project_section_id")
    task = Task(
        project_id=project_id,
        project_section_id=uuid.UUID(section_id) if section_id else None,
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "pending"),
        priority=data.get("priority", 0),
        phase=data.get("phase", "design"),
        dependencies=data.get("dependencies"),
        assignee_type=data.get("assignee_type"),
        assignee_name=data.get("assignee_name"),
        role=data.get("role"),
        model_tier=data.get("model_tier"),
        estimated_duration_seconds=data.get("estimated_duration_seconds"),
        validation_expectations=data.get("validation_expectations"),
    )
    db.session.add(task)
    db.session.flush()
    return task


def update_task(task: Task, data: dict) -> Task:
    mutable = (
        "title",
        "description",
        "status",
        "priority",
        "phase",
        "dependencies",
        "assignee_type",
        "assignee_name",
        "role",
        "model_tier",
        "estimated_duration_seconds",
        "validation_expectations",
        "completion_evidence",
    )
    for field in mutable:
        if field in data:
            setattr(task, field, data[field])
    if "project_section_id" in data:
        sid = data["project_section_id"]
        task.project_section_id = uuid.UUID(sid) if sid else None
    task.version += 1
    db.session.flush()
    return task


def claim_task(
    task_id: uuid.UUID,
    agent_name: str,
    duration: int = DEFAULT_LEASE_SECONDS,
) -> Task:
    now = datetime.now(UTC)
    new_until = now + timedelta(seconds=duration)

    # Succeed if task is pending (normal) or in_progress with an expired lease (recovery)
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(
            or_(
                and_(
                    Task.status == "pending",
                    or_(Task.claimed_until.is_(None), Task.claimed_until < now),
                ),
                and_(Task.status == "in_progress", Task.claimed_until < now),
            )
        )
        .values(
            status="in_progress",
            claimed_by=agent_name,
            claimed_until=new_until,
            lease_version=Task.lease_version + 1,
            version=Task.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise LeaseConflictError("Task is not available for claiming")

    db.session.flush()
    task = db.session.get(Task, task_id)
    assert task is not None
    project_status_service.advance_phase_if_needed(task.project_id, task.phase)
    events_service._record(
        event_type="task.claimed",
        project_id=task.project_id,
        task_id=task_id,
        actor_type="agent",
        actor_name=agent_name,
        payload={"duration_seconds": duration, "claimed_until": new_until.isoformat()},
    )
    return task


def heartbeat_task(
    task_id: uuid.UUID,
    agent_name: str,
    duration: int = DEFAULT_LEASE_SECONDS,
) -> Task:
    now = datetime.now(UTC)
    new_until = now + timedelta(seconds=duration)

    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.status == "in_progress")
        .where(Task.claimed_by == agent_name)
        .where(Task.claimed_until >= now)
        .values(claimed_until=new_until, version=Task.version + 1)
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise LeaseOwnershipError("Lease not held or expired")

    db.session.flush()
    task = db.session.get(Task, task_id)
    assert task is not None
    events_service._record(
        event_type="task.heartbeat",
        project_id=task.project_id,
        task_id=task_id,
        actor_type="agent",
        actor_name=agent_name,
        payload={"claimed_until": new_until.isoformat()},
    )
    return task


def complete_task(
    task_id: uuid.UUID,
    agent_name: str,
    evidence: str | None = None,
) -> Task:
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.status == "in_progress")
        .where(Task.claimed_by == agent_name)
        .values(
            status="completed",
            completion_evidence=evidence,
            claimed_by=None,
            claimed_until=None,
            version=Task.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise LeaseOwnershipError("Task not claimed by this agent or not in_progress")

    db.session.flush()
    task = db.session.get(Task, task_id)
    assert task is not None
    events_service._record(
        event_type="task.completed",
        project_id=task.project_id,
        task_id=task_id,
        actor_type="agent",
        actor_name=agent_name,
        payload={"evidence": evidence},
    )
    return task


def block_task(
    task_id: uuid.UUID,
    agent_name: str,
    reason: str | None = None,
) -> Task:
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.status == "in_progress")
        .where(Task.claimed_by == agent_name)
        .values(
            status="blocked",
            completion_evidence=reason,
            claimed_by=None,
            claimed_until=None,
            version=Task.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise LeaseOwnershipError("Task not claimed by this agent or not in_progress")

    db.session.flush()
    task = db.session.get(Task, task_id)
    assert task is not None
    events_service._record(
        event_type="task.blocked",
        project_id=task.project_id,
        task_id=task_id,
        actor_type="agent",
        actor_name=agent_name,
        payload={"reason": reason},
    )
    return task


# ── Task relationships ─────────────────────────────────────────────────────────

VALID_RELATIONSHIP_TYPES = frozenset({"blocks", "subtask_of", "duplicates", "relates_to"})


class RelationshipConflictError(Exception):
    pass


def list_relationships(task_id: uuid.UUID) -> list[TaskRelationship]:
    return list(
        db.session.scalars(
            select(TaskRelationship)
            .where(
                or_(
                    TaskRelationship.from_task_id == task_id,
                    TaskRelationship.to_task_id == task_id,
                )
            )
            .order_by(TaskRelationship.created_at)
        ).all()
    )


def get_relationship(rel_id: uuid.UUID) -> TaskRelationship | None:
    return db.session.get(TaskRelationship, rel_id)


def create_relationship(
    from_task_id: uuid.UUID, to_task_id: uuid.UUID, relationship_type: str
) -> TaskRelationship:
    rel = TaskRelationship(
        from_task_id=from_task_id,
        to_task_id=to_task_id,
        relationship_type=relationship_type,
    )
    db.session.add(rel)
    db.session.flush()
    return rel


def delete_relationship(rel: TaskRelationship) -> None:
    db.session.delete(rel)
    db.session.flush()
