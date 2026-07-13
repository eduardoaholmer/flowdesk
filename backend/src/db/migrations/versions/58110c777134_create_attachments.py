"""create attachments

Revision ID: 58110c777134
Revises: c12145ecad3c
Create Date: 2026-07-13 16:38:05.568032
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "58110c777134"
down_revision: str | None = "c12145ecad3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=True),
        sa.Column("comment_id", sa.Uuid(), nullable=True),
        sa.Column("uploader_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
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
        sa.CheckConstraint(
            "num_nonnulls(issue_id, comment_id) = 1", name="ck_attachments_exactly_one_parent"
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachments_comment_id", "attachments", ["comment_id"], unique=False)
    op.create_index("ix_attachments_issue_id", "attachments", ["issue_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_attachments_issue_id", table_name="attachments")
    op.drop_index("ix_attachments_comment_id", table_name="attachments")
    op.drop_table("attachments")
