"""Add role and model_tier fields to tasks table.

Revision ID: a2b3c4d5e6f7
Revises: f2a3b4c5d6e7
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("role", sa.String(length=64), nullable=True),
        schema="agent_workbench",
    )
    op.add_column(
        "tasks",
        sa.Column("model_tier", sa.String(length=32), nullable=True),
        schema="agent_workbench",
    )


def downgrade() -> None:
    op.drop_column("tasks", "model_tier", schema="agent_workbench")
    op.drop_column("tasks", "role", schema="agent_workbench")
