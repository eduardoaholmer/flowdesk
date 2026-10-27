"""create github_webhook_deliveries

Revision ID: 84416f31625b
Revises: ce37f86e65da
Create Date: 2026-10-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "84416f31625b"
down_revision: str | None = "ce37f86e65da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_webhook_deliveries",
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("installation_id", sa.BigInteger(), nullable=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column(
            "outcome",
            sa.Enum(
                "PROCESSED",
                "IGNORED",
                name="githubwebhookoutcome",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("delivery_id"),
    )
    op.create_index(
        "ix_github_webhook_deliveries_received_at",
        "github_webhook_deliveries",
        ["received_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_github_webhook_deliveries_received_at", table_name="github_webhook_deliveries"
    )
    op.drop_table("github_webhook_deliveries")
