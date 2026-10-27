"""create permission overrides

Revision ID: 31c66896669d
Revises: 43650f3d8613
Create Date: 2026-07-30 18:20:20.047278
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "31c66896669d"
down_revision: str | None = "43650f3d8613"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_VALUES = ["OWNER", "ADMIN", "MEMBER", "GUEST"]
_PERMISSION_VALUES = [
    "workspace.view",
    "workspace.update",
    "workspace.delete",
    "workspace.invite",
    "workspace.transfer_ownership",
    "workspace.manage_permissions",
    "member.remove",
    "member.update_role",
    "project.create",
    "project.read",
    "project.update",
    "project.delete",
    "issue.create",
    "issue.read",
    "issue.update",
    "issue.delete",
    "issue.assign",
    "issue.change_status",
    "comment.create",
    "comment.update",
    "comment.delete",
    "label.create",
    "label.read",
    "label.update",
    "label.delete",
    "workflow_state.read",
    "workflow_state.manage",
    "attachment.create",
    "attachment.delete",
]


def upgrade() -> None:
    op.create_table(
        "permission_overrides",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(*_ROLE_VALUES, name="workspacerole", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column(
            "permission",
            sa.Enum(*_PERMISSION_VALUES, name="permission", native_enum=False, length=64),
            nullable=False,
        ),
        sa.Column("granted", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_permission_overrides_workspace_role_permission",
        "permission_overrides",
        ["workspace_id", "role", "permission"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_permission_overrides_workspace_role_permission", table_name="permission_overrides"
    )
    op.drop_table("permission_overrides")
