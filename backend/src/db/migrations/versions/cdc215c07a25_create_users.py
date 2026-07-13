"""create users

Revision ID: cdc215c07a25
Revises:
Create Date: 2026-07-13 16:37:54.106808
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cdc215c07a25"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("avatar_url", sa.String(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_users_email_lower", "users", [sa.literal_column("lower(email)")], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_table("users")
