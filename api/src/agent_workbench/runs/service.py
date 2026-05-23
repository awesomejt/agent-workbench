from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import update

from ..database import db
from ..events import service as events_service
from .models import Run

_METRICS_KEYS = frozenset(
    {"model_id", "prompt_tokens", "completion_tokens", "latency_ms", "prompt_category"}
)


def _metrics(data: dict) -> dict:
    """Return only the runtime metrics keys that are present in data."""
    return {k: data[k] for k in _METRICS_KEYS if k in data}


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
        model_id=data.get("model_id"),
        prompt_tokens=data.get("prompt_tokens"),
        completion_tokens=data.get("completion_tokens"),
        latency_ms=data.get("latency_ms"),
        prompt_category=data.get("prompt_category"),
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
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    assert run is not None
    events_service._record(
        event_type="run.heartbeat",
        project_id=run.project_id,
        run_id=run_id,
        actor_type="agent",
        actor_name=run.agent_name,
    )
    return run


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
            **_metrics(data),
            version=Run.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    assert run is not None
    events_service._record(
        event_type="run.completed",
        project_id=run.project_id,
        run_id=run_id,
        actor_type="agent",
        actor_name=run.agent_name,
        payload={"summary": data.get("summary")},
    )
    return run


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
            **_metrics(data),
            version=Run.version + 1,
        )
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise RunStateError("Run is not in running state")
    db.session.flush()
    run = db.session.get(Run, run_id)
    assert run is not None
    events_service._record(
        event_type="run.failed",
        project_id=run.project_id,
        run_id=run_id,
        actor_type="agent",
        actor_name=run.agent_name,
        payload={"summary": data.get("summary")},
    )
    return run
