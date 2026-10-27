"""workspace-scope workflow_states, issue.status_id dinâmico

Revision ID: 43650f3d8613
Revises: c8f4a2b6e130
Create Date: 2026-07-29 12:00:00.000000

Reabre a ADR-035 (docs/09-decision-log.md) sem reativar `Team`/membership —
`workflow_states` (dormente desde a Sprint 2 em escopo de time) passa a ser
escopada diretamente por `workspace_id`, e `Issue.status` (enum fixo) vira
`Issue.status_id` (FK dinâmica), permitindo status customizados por workspace
(Sprint 9.2/ADR-056).

Ao contrário da migration `c573b41b553c` (podia ser destrutiva porque `issues`
ainda não tinha nenhuma linha real naquele ponto do projeto), esta migration
segue *expand -> backfill -> contract*: (1) reescopa `workflow_states` de
`team_id` para `workspace_id`; (2) semeia os 6 status atuais como linha real
por workspace existente, preservando nome/categoria/ordem/default; (3)
adiciona `issues.status_id` nullable, backfilla a partir do `status` (enum
antigo) via join pelo nome do status dentro do mesmo workspace, torna
`NOT NULL`, remove a coluna antiga.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from uuid6 import uuid7

revision: str = "43650f3d8613"
down_revision: str | None = "c8f4a2b6e130"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (nome novo do status, categoria, enum antigo correspondente, posição, é default)
_DEFAULT_STATES: tuple[tuple[str, str, str, int, bool], ...] = (
    ("Backlog", "BACKLOG", "BACKLOG", 0, True),
    ("Todo", "UNSTARTED", "TODO", 1, False),
    ("In Progress", "STARTED", "IN_PROGRESS", 2, False),
    ("In Review", "STARTED", "IN_REVIEW", 3, False),
    ("Done", "COMPLETED", "DONE", 4, False),
    ("Canceled", "CANCELED", "CANCELED", 5, False),
)

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

_workflow_states_table = sa.table(
    "workflow_states",
    sa.column("id", sa.Uuid()),
    sa.column("workspace_id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("category", sa.String()),
    sa.column("position", sa.Integer()),
    sa.column("is_default", sa.Boolean()),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Reescopar workflow_states de team_id para workspace_id.
    op.drop_index(
        "uq_workflow_states_team_id_default_active",
        table_name="workflow_states",
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_team_id_name_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_team_id_position_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute("ALTER TABLE workflow_states DROP CONSTRAINT IF EXISTS workflow_states_team_id_fkey")
    op.drop_column("workflow_states", "team_id")

    op.create_index(
        "uq_workflow_states_workspace_id_name_active",
        "workflow_states",
        ["workspace_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_workflow_states_workspace_id_position_active",
        "workflow_states",
        ["workspace_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_workflow_states_workspace_id_default_active",
        "workflow_states",
        ["workspace_id"],
        unique=True,
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )

    # 2. Semear os 6 status atuais como linha real por workspace existente.
    workspace_ids = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT id FROM workspaces WHERE deleted_at IS NULL")
        ).fetchall()
    ]
    now = datetime.now(UTC)
    rows_to_insert = []
    for workspace_id in workspace_ids:
        for name, category, _enum_value, position, is_default in _DEFAULT_STATES:
            rows_to_insert.append(
                {
                    "id": uuid7(),
                    "workspace_id": workspace_id,
                    "name": name,
                    "category": category,
                    "position": position,
                    "is_default": is_default,
                    "created_at": now,
                    "updated_at": now,
                }
            )
    if rows_to_insert:
        op.bulk_insert(_workflow_states_table, rows_to_insert)

    # 3. issues.status_id — expand, backfill, contract.
    op.add_column("issues", sa.Column("status_id", sa.Uuid(), nullable=True))
    for name, _category, enum_value, _position, _is_default in _DEFAULT_STATES:
        op.execute(
            sa.text(
                "UPDATE issues SET status_id = ws.id "
                "FROM workflow_states ws "
                "WHERE issues.workspace_id = ws.workspace_id "
                "AND ws.name = :name "
                "AND ws.deleted_at IS NULL "
                "AND issues.status = :enum_value"
            ).bindparams(name=name, enum_value=enum_value)
        )
    op.alter_column("issues", "status_id", nullable=False)

    op.drop_index("ix_issues_workspace_id_status_deleted_at", table_name="issues")
    op.drop_column("issues", "status")
    op.create_foreign_key(
        "issues_status_id_fkey",
        "issues",
        "workflow_states",
        ["status_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_issues_workspace_id_status_id_deleted_at",
        "issues",
        ["workspace_id", "status_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    """Best-effort: qualquer status customizado criado depois da Sprint 9.2
    (sem correspondência com os 6 nomes padrão) é mapeado para `BACKLOG` — uma
    reversão para enum fixo não consegue preservar customização real. Aceitável
    para o ciclo `upgrade -> downgrade -> upgrade` de verificação (CLAUDE.md §16)
    contra dado sem customização; não é uma operação sem perda em produção real.
    """
    bind = op.get_bind()

    op.drop_index("ix_issues_workspace_id_status_id_deleted_at", table_name="issues")
    op.execute("ALTER TABLE issues DROP CONSTRAINT IF EXISTS issues_status_id_fkey")

    op.add_column("issues", sa.Column("status", _ISSUE_STATUS, nullable=True))
    for name, _category, enum_value, _position, _is_default in _DEFAULT_STATES:
        op.execute(
            sa.text(
                "UPDATE issues SET status = :enum_value "
                "FROM workflow_states ws "
                "WHERE issues.workspace_id = ws.workspace_id "
                "AND issues.status_id = ws.id "
                "AND ws.name = :name"
            ).bindparams(name=name, enum_value=enum_value)
        )
    bind.execute(sa.text("UPDATE issues SET status = 'BACKLOG' WHERE status IS NULL"))
    op.alter_column("issues", "status", nullable=False)

    op.drop_column("issues", "status_id")

    # Remove as linhas semeadas pela `upgrade()` — sem isso, um `upgrade()`
    # seguinte tentaria semear de novo e colidiria com o índice único
    # `(workspace_id, name)`. Best-effort mesmo aqui: um workspace que tenha
    # renomeado um dos 6 status padrão não terá mais esse nome removido
    # (permanece como schema órfão team-scoped, inofensivo).
    bind.execute(
        sa.text("DELETE FROM workflow_states WHERE name IN :names").bindparams(
            sa.bindparam("names", value=[name for name, *_ in _DEFAULT_STATES], expanding=True)
        )
    )

    op.create_index(
        "ix_issues_workspace_id_status_deleted_at",
        "issues",
        ["workspace_id", "status", "deleted_at"],
        unique=False,
    )

    op.add_column("workflow_states", sa.Column("team_id", sa.Uuid(), nullable=True))
    op.drop_index(
        "uq_workflow_states_workspace_id_default_active",
        table_name="workflow_states",
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_workspace_id_position_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "uq_workflow_states_workspace_id_name_active",
        table_name="workflow_states",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_foreign_key(
        "workflow_states_team_id_fkey",
        "workflow_states",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="RESTRICT",
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
