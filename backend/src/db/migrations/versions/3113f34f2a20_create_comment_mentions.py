"""create comment mentions

Revision ID: 3113f34f2a20
Revises: f5044a958f94
Create Date: 2026-07-14 10:00:10.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3113f34f2a20"
down_revision: str | None = "f5044a958f94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comment_mentions",
        sa.Column("comment_id", sa.Uuid(), nullable=False),
        sa.Column("mentioned_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentioned_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id", "mentioned_user_id"),
    )


def downgrade() -> None:
    op.drop_table("comment_mentions")
