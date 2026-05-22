"""add estimated_duration_seconds to tasks

Revision ID: a1b2c3d4e5f6
Revises: eb91537942a2
Create Date: 2026-05-22 22:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'eb91537942a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tasks',
        sa.Column('estimated_duration_seconds', sa.Integer(), nullable=True),
        schema='agent_workbench',
    )


def downgrade() -> None:
    op.drop_column('tasks', 'estimated_duration_seconds', schema='agent_workbench')
