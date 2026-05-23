"""Add task_relationships table for modeling inter-task dependencies.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "task_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("from_task_id", sa.Uuid(), nullable=False),
        sa.Column("to_task_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["from_task_id"],
            ["agent_workbench.tasks.id"],
            name=op.f("fk_task_relationships_from_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_task_id"],
            ["agent_workbench.tasks.id"],
            name=op.f("fk_task_relationships_to_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_relationships")),
        sa.UniqueConstraint(
            "from_task_id",
            "to_task_id",
            "relationship_type",
            name="uq_task_rel_from_to_type",
        ),
        schema="agent_workbench",
    )
    op.create_index(
        op.f("ix_agent_workbench_task_relationships_from_task_id"),
        "task_relationships",
        ["from_task_id"],
        unique=False,
        schema="agent_workbench",
    )
    op.create_index(
        op.f("ix_agent_workbench_task_relationships_to_task_id"),
        "task_relationships",
        ["to_task_id"],
        unique=False,
        schema="agent_workbench",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_agent_workbench_task_relationships_to_task_id"),
        table_name="task_relationships",
        schema="agent_workbench",
    )
    op.drop_index(
        op.f("ix_agent_workbench_task_relationships_from_task_id"),
        table_name="task_relationships",
        schema="agent_workbench",
    )
    op.drop_table("task_relationships", schema="agent_workbench")
