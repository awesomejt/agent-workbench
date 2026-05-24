from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import SCHEMA, db


def _now() -> datetime:
    return datetime.now(UTC)


class AiServer(db.Model):  # type: ignore[name-defined]
    __tablename__ = "ai_servers"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    server_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", index=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # TODO: store model list once probe fetches /api/tags (Ollama) or /v1/models (LiteLLM/oMLX)
    server_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
