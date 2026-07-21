"""add key to projects

Revision ID: b3e7c1a9d240
Revises: f4c36aa63332
Create Date: 2026-07-21 10:00:00.000000

`key` (2-4 letras maiúsculas, decorativa — sem relação com `FD-{n}` de Issue,
ver ADR-049) é adicionada diretamente como `NOT NULL`, mesmo padrão da
migration irmã `fc0a10c66145` que adicionou `slug`/`created_by` sem o ciclo
"nullable -> backfill -> NOT NULL": a suíte de migração roda contra um banco
limpo (`alembic upgrade head` em CI), então não há linha legada a preservar
aqui. O índice único parcial espelha exatamente `uq_projects_workspace_id_slug_active`
(único por workspace apenas entre projetos ativos, `deleted_at IS NULL`).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3e7c1a9d240"
down_revision: str | None = "f4c36aa63332"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("key", sa.String(), nullable=False))
    op.create_index(
        "uq_projects_workspace_id_key_active",
        "projects",
        ["workspace_id", "key"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_projects_workspace_id_key_active", table_name="projects")
    op.drop_column("projects", "key")
