"""create issues

Revision ID: e471449c3682
Revises: 8e0f2eb0ad76
Create Date: 2026-07-13 16:38:00.303011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e471449c3682"
down_revision: str | None = "8e0f2eb0ad76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issues",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status_id", sa.Uuid(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum(
                "NO_PRIORITY",
                "LOW",
                "MEDIUM",
                "HIGH",
                "URGENT",
                name="issuepriority",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["status_id"], ["workflow_states.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_issues_assignee_id_deleted_at", "issues", ["assignee_id", "deleted_at"], unique=False
    )
    op.create_index(
        "ix_issues_team_id_status_id_deleted_at",
        "issues",
        ["team_id", "status_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_issues_title_description_fts",
        "issues",
        [sa.literal_column("to_tsvector('simple', title || ' ' || coalesce(description, ''))")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_issues_workspace_id_deleted_at_updated_at",
        "issues",
        ["workspace_id", "deleted_at", sa.literal_column("updated_at DESC")],
        unique=False,
    )
    op.create_index("uq_issues_team_id_number", "issues", ["team_id", "number"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_issues_team_id_number", table_name="issues")
    op.drop_index("ix_issues_workspace_id_deleted_at_updated_at", table_name="issues")
    op.drop_index("ix_issues_title_description_fts", table_name="issues", postgresql_using="gin")
    op.drop_index("ix_issues_team_id_status_id_deleted_at", table_name="issues")
    op.drop_index("ix_issues_assignee_id_deleted_at", table_name="issues")
    op.drop_table("issues")
