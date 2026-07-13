"""create workspaces

Revision ID: 86dc5d2ef0c8
Revises: 05383634b2af
Create Date: 2026-07-13 16:37:56.173668
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "86dc5d2ef0c8"
down_revision: str | None = "05383634b2af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_workspaces_slug_active",
        "workspaces",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "ADMIN",
                "MEMBER",
                "GUEST",
                name="workspacerole",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"], unique=False)
    op.create_index(
        "ix_workspace_members_workspace_id_deleted_at",
        "workspace_members",
        ["workspace_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "uq_workspace_members_workspace_id_user_id_active",
        "workspace_members",
        ["workspace_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "invitations",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "ADMIN",
                "MEMBER",
                "GUEST",
                name="workspacerole",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("invited_by_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "uq_invitations_workspace_id_email_pending",
        "invitations",
        ["workspace_id", "email"],
        unique=True,
        postgresql_where=sa.text("accepted_at IS NULL AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_invitations_workspace_id_email_pending",
        table_name="invitations",
        postgresql_where=sa.text("accepted_at IS NULL AND deleted_at IS NULL"),
    )
    op.drop_table("invitations")
    op.drop_index(
        "uq_workspace_members_workspace_id_user_id_active",
        table_name="workspace_members",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index("ix_workspace_members_workspace_id_deleted_at", table_name="workspace_members")
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_index(
        "uq_workspaces_slug_active",
        table_name="workspaces",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("workspaces")
