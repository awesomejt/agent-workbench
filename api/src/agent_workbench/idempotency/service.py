from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from ..database import db
from .models import IdempotencyRecord

_TTL_HOURS = 24


def check_key(key: str, endpoint: str, actor_name: str) -> dict | None:
    """Return the stored response dict if an unexpired record exists, else None."""
    cutoff = datetime.now(UTC) - timedelta(hours=_TTL_HOURS)
    record = db.session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == key,
            IdempotencyRecord.endpoint == endpoint,
            IdempotencyRecord.actor_name == actor_name,
            IdempotencyRecord.created_at > cutoff,
        )
    )
    if record is None:
        return None
    return {"status": record.response_status, "body": record.response_body}


def store_key(
    key: str,
    endpoint: str,
    actor_name: str,
    response_status: int,
    response_body: str,
) -> None:
    """Persist a response for future replay.  Caller must commit the session."""
    record = IdempotencyRecord(
        idempotency_key=key,
        endpoint=endpoint,
        actor_name=actor_name,
        response_status=response_status,
        response_body=response_body,
    )
    db.session.add(record)
