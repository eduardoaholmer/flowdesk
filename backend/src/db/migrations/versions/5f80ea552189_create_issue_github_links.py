"""create issue_github_links

Revision ID: 5f80ea552189
Revises: 84416f31625b
Create Date: 2026-10-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5f80ea552189"
down_revision: str | None = "84416f31625b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issue_github_links",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("pull_request_id", sa.BigInteger(), nullable=False),
        sa.Column("repository_full_name", sa.String(), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_url", sa.String(), nullable=False),
        sa.Column("pr_title", sa.String(), nullable=False),
        sa.Column(
            "pr_state",
            sa.Enum(
                "OPEN",
                "DRAFT",
                "MERGED",
                "CLOSED",
                name="githubpullrequeststate",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("author_login", sa.String(), nullable=False),
        sa.Column("head_branch", sa.String(), nullable=False),
        sa.Column("pr_updated_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_issue_github_links_workspace_id_pull_request_id",
        "issue_github_links",
        ["workspace_id", "pull_request_id"],
        unique=False,
    )
    op.create_index(
        "uq_issue_github_links_issue_id_pull_request_id",
        "issue_github_links",
        ["issue_id", "pull_request_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_issue_github_links_issue_id_pull_request_id", table_name="issue_github_links")
    op.drop_index(
        "ix_issue_github_links_workspace_id_pull_request_id", table_name="issue_github_links"
    )
    op.drop_table("issue_github_links")
