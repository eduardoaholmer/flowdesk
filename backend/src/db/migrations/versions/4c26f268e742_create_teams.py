"""create teams

Revision ID: 4c26f268e742
Revises: 86dc5d2ef0c8
Create Date: 2026-07-13 16:37:57.174395
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4c26f268e742"
down_revision: str | None = "86dc5d2ef0c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
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
        "uq_teams_workspace_id_key_active",
        "teams",
        ["workspace_id", "key"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "team_members",
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_team_members_team_id_user_id_active",
        "team_members",
        ["team_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "workflow_states",
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "BACKLOG",
                "UNSTARTED",
                "STARTED",
                "COMPLETED",
                "CANCELED",
                name="workflowstatecategory",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_workflow_states_team_id_default_active",
        "workflow_states",
        ["team_id"],
        unique=True,
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )
    op.create_index(
        "uq_workflow_states_team_id_name_active",
        "workflow_states",
        ["team_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_workflow_states_team_id_position_active",
        "workflow_states",
        ["team_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "team_issue_counters",
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("next_number", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("team_id"),
    )


def downgrade() -> None:
    op.drop_table("team_issue_counters")
    op.drop_index(
        "uq_workflow_states_team_id_position_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_team_id_name_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_team_id_default_active",
        table_name="workflow_states",
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )
    op.drop_table("workflow_states")
    op.drop_index(
        "uq_team_members_team_id_user_id_active",
        table_name="team_members",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("team_members")
    op.drop_index(
        "uq_teams_workspace_id_key_active",
        table_name="teams",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("teams")
