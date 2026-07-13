"""create labels

Revision ID: 8e0f2eb0ad76
Revises: 5b0379d95061
Create Date: 2026-07-13 16:37:59.262289
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e0f2eb0ad76"
down_revision: str | None = "5b0379d95061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_labels_workspace_id_name_active",
        "labels",
        ["workspace_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_labels_workspace_id_name_active",
        table_name="labels",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("labels")
