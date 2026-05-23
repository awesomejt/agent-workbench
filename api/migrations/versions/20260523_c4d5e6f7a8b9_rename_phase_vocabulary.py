"""Rename phase vocabulary: research→discovery, planning→design.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    for table in ("tasks", "project_statuses"):
        op.execute(
            f"UPDATE agent_workbench.{table} SET phase = 'discovery' WHERE phase = 'research'"
        )
        op.execute(
            f"UPDATE agent_workbench.{table} SET phase = 'design' WHERE phase = 'planning'"
        )


def downgrade() -> None:
    for table in ("tasks", "project_statuses"):
        op.execute(
            f"UPDATE agent_workbench.{table} SET phase = 'research' WHERE phase = 'discovery'"
        )
        op.execute(
            f"UPDATE agent_workbench.{table} SET phase = 'planning' WHERE phase = 'design'"
        )
