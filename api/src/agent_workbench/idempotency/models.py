from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import SCHEMA, db


def _now() -> datetime:
    return datetime.now(UTC)


class IdempotencyRecord(db.Model):  # type: ignore[name-defined]
    """Stores replayed responses for idempotent agent commands.

    Uniqueness is scoped to (idempotency_key, endpoint, actor_name) so different
    agents can use the same key without interfering, and the same agent can reuse
    a key on a different endpoint.  Records expire after 24 hours (checked on read).
    """

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key", "endpoint", "actor_name", name="uq_idem_key_endpoint_actor"
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
