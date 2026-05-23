"""Add runtime metrics fields to runs table.

Revision ID: d9e0f1a2b3c4
Revises: c8e1f2a3b4d5
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, None] = "c8e1f2a3b4d5"
branch_labels = None
depends_on = None

SCHEMA = "agent_workbench"


def upgrade() -> None:
    op.add_column("runs", sa.Column("model_id", sa.String(128), nullable=True), schema=SCHEMA)
    op.add_column(
        "runs", sa.Column("prompt_tokens", sa.Integer(), nullable=True), schema=SCHEMA
    )
    op.add_column(
        "runs", sa.Column("completion_tokens", sa.Integer(), nullable=True), schema=SCHEMA
    )
    op.add_column("runs", sa.Column("latency_ms", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column(
        "runs", sa.Column("prompt_category", sa.String(64), nullable=True), schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_column("runs", "prompt_category", schema=SCHEMA)
    op.drop_column("runs", "latency_ms", schema=SCHEMA)
    op.drop_column("runs", "completion_tokens", schema=SCHEMA)
    op.drop_column("runs", "prompt_tokens", schema=SCHEMA)
    op.drop_column("runs", "model_id", schema=SCHEMA)
