"""add description to workspaces

Revision ID: 56d54b9ad393
Revises: 58110c777134
Create Date: 2026-07-13 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "56d54b9ad393"
down_revision: str | None = "58110c777134"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("description", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("workspaces", "description")
