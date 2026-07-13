"""create comments

Revision ID: c208f28527f5
Revises: 3bce4084eea4
Create Date: 2026-07-13 16:38:02.476766
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c208f28527f5"
down_revision: str | None = "3bce4084eea4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comments_issue_id_deleted_at_created_at",
        "comments",
        ["issue_id", "deleted_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comments_issue_id_deleted_at_created_at", table_name="comments")
    op.drop_table("comments")
