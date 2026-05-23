"""Extend task status state machine: add new/in_progress/rejected/duplicate statuses.

Transition any tasks with an active lease (claimed_by IS NOT NULL and
claimed_until > NOW()) from 'pending' to 'in_progress', since those tasks are
actively held by an agent under the old model.

Revision ID: e1f2a3b4c5d6
Revises: d9e0f1a2b3c4
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d9e0f1a2b3c4"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE agent_workbench.tasks
        SET status = 'in_progress'
        WHERE status = 'pending'
          AND claimed_by IS NOT NULL
          AND claimed_until > NOW()
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE agent_workbench.tasks
        SET status = 'pending'
        WHERE status = 'in_progress'
    """)
