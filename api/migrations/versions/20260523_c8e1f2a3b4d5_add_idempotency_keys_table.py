"""add_idempotency_keys_table

Revision ID: c8e1f2a3b4d5
Revises: a1b2c3d4e5f6
Create Date: 2026-05-23 00:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8e1f2a3b4d5"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "agent_workbench"


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("endpoint", sa.String(length=64), nullable=False),
        sa.Column("actor_name", sa.String(length=128), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_keys"),
        sa.UniqueConstraint(
            "idempotency_key", "endpoint", "actor_name", name="uq_idem_key_endpoint_actor"
        ),
        schema=SCHEMA,
    )

    op.drop_index("ix_agent_workbench_tasks_idempotency_key", table_name="tasks", schema=SCHEMA)
    op.drop_column("tasks", "idempotency_key", schema=SCHEMA)


def downgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_agent_workbench_tasks_idempotency_key",
        "tasks",
        ["idempotency_key"],
        unique=True,
        schema=SCHEMA,
    )

    op.drop_table("idempotency_keys", schema=SCHEMA)
