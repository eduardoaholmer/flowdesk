"""add parent_id to issues

Revision ID: e2c2c5c8594a
Revises: 31c66896669d
Create Date: 2026-07-30 19:32:45.038415
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2c2c5c8594a"
down_revision: str | None = "31c66896669d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("issues", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.create_index(
        "ix_issues_parent_id_deleted_at", "issues", ["parent_id", "deleted_at"], unique=False
    )
    op.create_foreign_key(
        "issues_parent_id_fkey", "issues", "issues", ["parent_id"], ["id"], ondelete="RESTRICT"
    )


def downgrade() -> None:
    op.drop_constraint("issues_parent_id_fkey", "issues", type_="foreignkey")
    op.drop_index("ix_issues_parent_id_deleted_at", table_name="issues")
    op.drop_column("issues", "parent_id")
