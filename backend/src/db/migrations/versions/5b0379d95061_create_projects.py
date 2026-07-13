"""create projects

Revision ID: 5b0379d95061
Revises: 4c26f268e742
Create Date: 2026-07-13 16:37:58.246799
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5b0379d95061"
down_revision: str | None = "4c26f268e742"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PLANNED",
                "IN_PROGRESS",
                "COMPLETED",
                "CANCELED",
                name="projectstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_projects_workspace_id_deleted_at",
        "projects",
        ["workspace_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_projects_workspace_id_deleted_at", table_name="projects")
    op.drop_table("projects")
