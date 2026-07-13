"""create activity logs

Revision ID: 74d9c63228bc
Revises: c208f28527f5
Create Date: 2026-07-13 16:38:03.546812
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "74d9c63228bc"
down_revision: str | None = "c208f28527f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=True),
        sa.Column("old_value", sa.String(), nullable=True),
        sa.Column("new_value", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_activity_logs_issue_id_created_at",
        "activity_logs",
        ["issue_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_issue_id_created_at", table_name="activity_logs")
    op.drop_table("activity_logs")
