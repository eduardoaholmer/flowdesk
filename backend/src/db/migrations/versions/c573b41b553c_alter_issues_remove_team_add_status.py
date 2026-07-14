"""alter issues remove team add status

Revision ID: c573b41b553c
Revises: 0aa72aead06a
Create Date: 2026-07-14 10:00:00.000000

Redesenha `issues` para a Sprint 7 (Núcleo de Issues): remove a dependência de
`Team`/`WorkflowState` (nunca ganharam service/router, ver ADR-012 em
docs/09-decision-log.md), substitui `status_id` por um enum fixo `status`, troca
a unicidade de `number` de `(team_id, number)` para `(workspace_id, number)` e
adiciona `estimate`/`due_date`. Migration destrutiva direta (sem
*expand -> backfill -> contract*) porque `issues` nunca recebeu linha em
produção — mesma justificativa já usada para `Project.status` na Sprint 6
(migration `fc0a10c66145`).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c573b41b553c"
down_revision: str | None = "0aa72aead06a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ISSUE_STATUS = sa.Enum(
    "BACKLOG",
    "TODO",
    "IN_PROGRESS",
    "IN_REVIEW",
    "DONE",
    "CANCELED",
    name="issuestatus",
    native_enum=False,
    length=32,
)


def upgrade() -> None:
    op.drop_index("uq_issues_team_id_number", table_name="issues")
    op.drop_index("ix_issues_team_id_status_id_deleted_at", table_name="issues")

    op.execute("ALTER TABLE issues DROP CONSTRAINT IF EXISTS issues_team_id_fkey")
    op.execute("ALTER TABLE issues DROP CONSTRAINT IF EXISTS issues_status_id_fkey")
    op.drop_column("issues", "team_id")
    op.drop_column("issues", "status_id")

    op.add_column("issues", sa.Column("status", _ISSUE_STATUS, nullable=False))
    op.add_column("issues", sa.Column("estimate", sa.Integer(), nullable=True))
    op.add_column("issues", sa.Column("due_date", sa.Date(), nullable=True))

    op.create_index(
        "uq_issues_workspace_id_number", "issues", ["workspace_id", "number"], unique=True
    )
    op.create_index(
        "ix_issues_workspace_id_status_deleted_at",
        "issues",
        ["workspace_id", "status", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_issues_creator_id_deleted_at", "issues", ["creator_id", "deleted_at"], unique=False
    )
    op.create_index(
        "ix_issues_project_id_deleted_at", "issues", ["project_id", "deleted_at"], unique=False
    )

    op.create_table(
        "workspace_issue_counters",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("workspace_id"),
    )


def downgrade() -> None:
    op.drop_table("workspace_issue_counters")

    op.drop_index("ix_issues_project_id_deleted_at", table_name="issues")
    op.drop_index("ix_issues_creator_id_deleted_at", table_name="issues")
    op.drop_index("ix_issues_workspace_id_status_deleted_at", table_name="issues")
    op.drop_index("uq_issues_workspace_id_number", table_name="issues")

    op.drop_column("issues", "due_date")
    op.drop_column("issues", "estimate")
    op.drop_column("issues", "status")

    op.add_column("issues", sa.Column("status_id", sa.Uuid(), nullable=True))
    op.add_column("issues", sa.Column("team_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "issues_status_id_fkey",
        "issues",
        "workflow_states",
        ["status_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "issues_team_id_fkey", "issues", "teams", ["team_id"], ["id"], ondelete="RESTRICT"
    )

    op.create_index(
        "ix_issues_team_id_status_id_deleted_at",
        "issues",
        ["team_id", "status_id", "deleted_at"],
        unique=False,
    )
    op.create_index("uq_issues_team_id_number", "issues", ["team_id", "number"], unique=True)
