"""create label activity logs

Revision ID: f5044a958f94
Revises: a7c1d9f0b2e4
Create Date: 2026-07-14 10:00:05.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f5044a958f94"
down_revision: str | None = "a7c1d9f0b2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "label_activity_logs",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_label_activity_logs_label_id_created_at",
        "label_activity_logs",
        ["label_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_label_activity_logs_label_id_created_at", table_name="label_activity_logs")
    op.drop_table("label_activity_logs")
