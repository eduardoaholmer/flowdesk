"""create issue labels

Revision ID: 3bce4084eea4
Revises: e471449c3682
Create Date: 2026-07-13 16:38:01.395992
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3bce4084eea4"
down_revision: str | None = "e471449c3682"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issue_labels",
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("issue_id", "label_id"),
    )


def downgrade() -> None:
    op.drop_table("issue_labels")
