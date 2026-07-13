"""create notifications

Revision ID: c12145ecad3c
Revises: 74d9c63228bc
Create Date: 2026-07-13 16:38:04.524210
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c12145ecad3c"
down_revision: str | None = "74d9c63228bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "MENTION",
                "ASSIGNMENT",
                "STATUS_CHANGE",
                name="notificationtype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_id_read_at_created_at",
        "notifications",
        ["user_id", "read_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id_read_at_created_at", table_name="notifications")
    op.drop_table("notifications")
