from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select

from ..database import db
from .models import AiServer


def list_servers(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    available: bool = False,
) -> tuple[list[AiServer], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(AiServer)
    if available:
        base = base.where(AiServer.status == "up")
    elif status:
        base = base.where(AiServer.status == status)
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(base.order_by(AiServer.name).offset(offset).limit(per_page)).all()
    return list(items), total


def get_server(server_id: uuid.UUID) -> AiServer | None:
    return db.session.get(AiServer, server_id)


def get_server_by_name(name: str) -> AiServer | None:
    return db.session.scalar(select(AiServer).where(AiServer.name == name))


def create_server(data: dict) -> AiServer:
    server = AiServer(
        name=data["name"],
        url=data["url"],
        server_type=data["server_type"],
        notes=data.get("notes"),
        server_metadata=data.get("metadata"),
    )
    db.session.add(server)
    db.session.flush()
    return server


def update_server(server: AiServer, data: dict) -> AiServer:
    mutable = ("name", "url", "server_type", "notes")
    for field in mutable:
        if field in data:
            setattr(server, field, data[field])
    if "metadata" in data:
        server.server_metadata = data["metadata"]
    if "status" in data:
        server.status = data["status"]
        server.last_checked_at = datetime.now(UTC)
        if data["status"] == "up":
            server.last_up_at = server.last_checked_at
        server.last_error = data.get("last_error")
    server.version += 1
    db.session.flush()
    return server


def delete_server(server: AiServer) -> None:
    db.session.delete(server)
    db.session.flush()
