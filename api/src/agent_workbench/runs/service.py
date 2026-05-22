from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import update

from ..database import db
from .models import Run


class RunStateError(Exception):
    pass


def get_run(run_id: uuid.UUID) -> Run | None:
    return db.session.get(Run, run_id)


def create_run(data: dict) -> Run:
    task_id = data.get("task_id")
    run = Run(
        project_id=uuid.UUID(data["project_id"]),
        task_id=uuid.UUID(task_id) if task_id else None,
        agent_name=data["agent_name"],
        status="running",
        validation_commands=data.get("validation_commands"),
        summary=data.get("summary"),
    )
    db.session.add(run)
    db.session.flush()
    return run


def heartbeat_run(run_id: uuid.UUID) -> Run:
    now = datetime.now(UTC)
    result = db.session.execute(
        update(Run)
        .where(Run.id == run_id)
        .where(Run.status == "running")
        .values(last_heartbeat_at=now, version=Run.version + 1)
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    return run  # type: ignore[return-value]


def complete_run(run_id: uuid.UUID, data: dict) -> Run:
    now = datetime.now(UTC)
    result = db.session.execute(
        update(Run)
        .where(Run.id == run_id)
        .where(Run.status == "running")
        .values(
            status="completed",
            completed_at=now,
            validation_result=data.get("validation_result"),
            summary=data.get("summary"),
            version=Run.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    return run  # type: ignore[return-value]


def fail_run(run_id: uuid.UUID, data: dict) -> Run:
    now = datetime.now(UTC)
    result = db.session.execute(
        update(Run)
        .where(Run.id == run_id)
        .where(Run.status == "running")
        .values(
            status="failed",
            completed_at=now,
            validation_result=data.get("validation_result"),
            summary=data.get("summary"),
            version=Run.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    return run  # type: ignore[return-value]
