"""Add ai_servers table for local AI server availability tracking.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_servers",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("server_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("name", name="uq_ai_servers_name"),
        schema="agent_workbench",
    )
    op.create_index(
        "ix_ai_servers_name", "ai_servers", ["name"], schema="agent_workbench"
    )
    op.create_index(
        "ix_ai_servers_status", "ai_servers", ["status"], schema="agent_workbench"
    )


def downgrade() -> None:
    op.drop_index("ix_ai_servers_status", table_name="ai_servers", schema="agent_workbench")
    op.drop_index("ix_ai_servers_name", table_name="ai_servers", schema="agent_workbench")
    op.drop_table("ai_servers", schema="agent_workbench")
