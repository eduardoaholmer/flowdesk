"""create project members

Revision ID: c8f4a2b6e130
Revises: b3e7c1a9d240
Create Date: 2026-07-21 10:05:00.000000

`project_members` é uma associação informativa usuário<->projeto (ADR-049) —
NÃO um mecanismo de controle de acesso. Sem soft delete nem `updated_at`
(membership é add/remove, não arquivada). Índice único em
`(project_id, user_id)` para tornar o `add_member` idempotente no banco.
FKs `RESTRICT` para `projects`/`users`, alinhadas ao resto do schema.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8f4a2b6e130"
down_revision: str | None = "b3e7c1a9d240"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_project_members_project_id_user_id",
        "project_members",
        ["project_id", "user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_project_members_project_id_user_id", table_name="project_members")
    op.drop_table("project_members")
