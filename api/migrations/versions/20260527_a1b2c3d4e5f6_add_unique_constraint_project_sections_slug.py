"""add unique constraint on project_sections(project_id, slug)

Revision ID: a6b7c8d9e0f1
Revises: d5e6f7a8b9c0
Create Date: 2026-05-27

"""

from __future__ import annotations

from alembic import op

revision = "a6b7c8d9e0f1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_project_sections_project_slug",
        "project_sections",
        ["project_id", "slug"],
        schema="agent_workbench",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_sections_project_slug",
        "project_sections",
        schema="agent_workbench",
        type_="unique",
    )
