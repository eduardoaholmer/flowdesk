"""create oauth_identities

Revision ID: a5e7fc73c034
Revises: e2c2c5c8594a
Create Date: 2026-09-08 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a5e7fc73c034"
down_revision: str | None = "e2c2c5c8594a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=True)

    op.create_table(
        "oauth_identities",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_identities_provider_provider_user_id",
        "oauth_identities",
        ["provider", "provider_user_id"],
        unique=True,
    )
    op.create_index("ix_oauth_identities_user_id", "oauth_identities", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_oauth_identities_user_id", table_name="oauth_identities")
    op.drop_index("ix_oauth_identities_provider_provider_user_id", table_name="oauth_identities")
    op.drop_table("oauth_identities")

    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=False)
