from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update

from ..database import db
from .models import Task

_DEFAULT_LEASE_SECONDS = 900  # 15 minutes


class LeaseConflictError(Exception):
    pass


class LeaseOwnershipError(Exception):
    pass


def list_tasks(
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    phase: str | None = None,
) -> tuple[list[Task], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(Task).where(Task.project_id == project_id)
    if status:
        base = base.where(Task.status == status)
    if phase:
        base = base.where(Task.phase == phase)
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
        phase=data.get("phase", "planning"),
        dependencies=data.get("dependencies"),
        assignee_type=data.get("assignee_type"),
        assignee_name=data.get("assignee_name"),
        validation_expectations=data.get("validation_expectations"),
    )
    db.session.add(task)
    db.session.flush()
    return task


def update_task(task: Task, data: dict) -> Task:
    mutable = (
        "title", "description", "status", "priority", "phase",
        "dependencies", "assignee_type", "assignee_name",
        "validation_expectations", "completion_evidence",
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
    duration: int = _DEFAULT_LEASE_SECONDS,
    idempotency_key: str | None = None,
) -> Task:
    now = datetime.now(UTC)
    new_until = now + timedelta(seconds=duration)

    # Atomic update: only succeeds if no unexpired lease from another agent
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.status == "pending")
        .where(
            or_(
                Task.claimed_until.is_(None),
                Task.claimed_until < now,
                Task.claimed_by == agent_name,
            )
        )
        .values(
            claimed_by=agent_name,
            claimed_until=new_until,
            lease_version=Task.lease_version + 1,
            idempotency_key=idempotency_key,
            version=Task.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise LeaseConflictError("Task is not available for claiming")

    db.session.flush()
    task = db.session.get(Task, task_id)
    return task  # type: ignore[return-value]


def heartbeat_task(
    task_id: uuid.UUID,
    agent_name: str,
    duration: int = _DEFAULT_LEASE_SECONDS,
) -> Task:
    now = datetime.now(UTC)
    new_until = now + timedelta(seconds=duration)

    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.claimed_by == agent_name)
        .where(Task.claimed_until >= now)
        .values(claimed_until=new_until, version=Task.version + 1)
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise LeaseOwnershipError("Lease not held or expired")

    db.session.flush()
    task = db.session.get(Task, task_id)
    return task  # type: ignore[return-value]


def complete_task(
    task_id: uuid.UUID,
    agent_name: str,
    evidence: str | None = None,
) -> Task:
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
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
    if result.rowcount == 0:
        raise LeaseOwnershipError("Task not claimed by this agent")

    db.session.flush()
    task = db.session.get(Task, task_id)
    return task  # type: ignore[return-value]


def block_task(
    task_id: uuid.UUID,
    agent_name: str,
    reason: str | None = None,
) -> Task:
    result = db.session.execute(
        update(Task)
        .where(Task.id == task_id)
        .where(Task.claimed_by == agent_name)
        .values(
            status="blocked",
            completion_evidence=reason,
            version=Task.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise LeaseOwnershipError("Task not claimed by this agent")

    db.session.flush()
    task = db.session.get(Task, task_id)
    return task  # type: ignore[return-value]
