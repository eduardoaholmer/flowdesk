"""add description to labels

Revision ID: a7c1d9f0b2e4
Revises: f42ae23f3ec0
Create Date: 2026-07-14 10:00:03.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c1d9f0b2e4"
down_revision: str | None = "f42ae23f3ec0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("labels", sa.Column("description", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("labels", "description")
