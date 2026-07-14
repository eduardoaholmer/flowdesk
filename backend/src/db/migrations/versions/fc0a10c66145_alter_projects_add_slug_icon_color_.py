"""alter projects: add slug/icon/color/created_by, redefine status

Revision ID: fc0a10c66145
Revises: c2792667d7f6
Create Date: 2026-07-13 19:10:00.000000

`status` não recebe nenhuma alteração de DDL aqui: a coluna já é
`VARCHAR(32)` sem `CHECK` constraint (`domain_enum()`, ver `src/db/base.py`,
não usa `create_constraint=True`) — os valores permitidos são só uma
convenção reforçada pela aplicação (Pydantic/enum Python), nunca pelo banco.
Redefinir `ProjectStatus` de `PLANNED/IN_PROGRESS/COMPLETED/CANCELED` para
`ACTIVE/ARCHIVED` (Sprint 6) é portanto uma mudança só em `models.py`.

`slug`/`created_by` são adicionados diretamente como `NOT NULL` sem o padrão
"adicionar nullable -> backfill -> tornar NOT NULL": a tabela `projects` nunca
recebeu uma linha em produção (a feature só tinha model+repository parciais
até esta sprint), então não há dado legado para preservar.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "fc0a10c66145"
down_revision: str | None = "c2792667d7f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("slug", sa.String(), nullable=False))
    op.add_column("projects", sa.Column("icon", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("color", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("created_by", sa.Uuid(), nullable=False))
    op.create_foreign_key(
        "projects_created_by_fkey", "projects", "users", ["created_by"], ["id"], ondelete="RESTRICT"
    )
    op.create_index(
        "uq_projects_workspace_id_slug_active",
        "projects",
        ["workspace_id", "slug"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_projects_workspace_id_name_active",
        "projects",
        ["workspace_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_projects_workspace_id_name_active", table_name="projects")
    op.drop_index("uq_projects_workspace_id_slug_active", table_name="projects")
    op.drop_constraint("projects_created_by_fkey", "projects", type_="foreignkey")
    op.drop_column("projects", "created_by")
    op.drop_column("projects", "color")
    op.drop_column("projects", "icon")
    op.drop_column("projects", "slug")
