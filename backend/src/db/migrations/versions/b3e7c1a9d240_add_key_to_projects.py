"""add key to projects

Revision ID: b3e7c1a9d240
Revises: f4c36aa63332
Create Date: 2026-07-21 10:00:00.000000

`key` (2-4 letras maiúsculas, decorativa — sem relação com `FD-{n}` de Issue,
ver ADR-049) é adicionada `nullable` e passa por um backfill determinístico
(iniciais/prefixo do nome, mesmo espírito de `core/project_key.py::derive_project_key`
— reimplementado aqui, não importado, para manter a migration independente
de código de aplicação que pode mudar) antes de virar `NOT NULL`: ao contrário
da migration irmã `fc0a10c66145` (tabela `projects` ainda vazia naquela
sprint), esta já roda contra bases com projetos reais — `ADD COLUMN NOT NULL`
direto quebra com `NotNullViolationError` em qualquer banco não-vazio (achado
ao validar a Sprint 19.1 contra um Postgres de desenvolvimento real). O índice
único parcial espelha exatamente `uq_projects_workspace_id_slug_active`
(único por workspace apenas entre projetos ativos, `deleted_at IS NULL`);
colisão de key derivada dentro do mesmo workspace cai para uma key aleatória,
mesmo padrão de retry do `ProjectService` em runtime.
"""

import secrets
import string
import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3e7c1a9d240"
down_revision: str | None = "f4c36aa63332"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KEY_MIN_LENGTH = 2
_KEY_MAX_LENGTH = 4


def _derive_key(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = [word for word in normalized.replace("-", " ").split() if word.isalpha()]
    if len(words) >= _KEY_MIN_LENGTH:
        candidate = "".join(word[0] for word in words)[:_KEY_MAX_LENGTH].upper()
    elif words:
        candidate = words[0][:3].upper()
    else:
        candidate = ""
    while len(candidate) < _KEY_MIN_LENGTH:
        candidate += secrets.choice(string.ascii_uppercase)
    return candidate


def _random_key() -> str:
    return "".join(secrets.choice(string.ascii_uppercase) for _ in range(_KEY_MAX_LENGTH))


def upgrade() -> None:
    op.add_column("projects", sa.Column("key", sa.String(), nullable=True))

    connection = op.get_bind()
    projects = sa.table(
        "projects",
        sa.column("id", sa.Uuid()),
        sa.column("workspace_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
        sa.column("key", sa.String()),
    )
    rows = connection.execute(
        sa.select(projects.c.id, projects.c.workspace_id, projects.c.name, projects.c.deleted_at)
    ).fetchall()

    used_keys_by_workspace: dict[object, set[str]] = {}
    for row in rows:
        candidate = _derive_key(row.name)
        if row.deleted_at is None:
            used = used_keys_by_workspace.setdefault(row.workspace_id, set())
            while candidate in used:
                candidate = _random_key()
            used.add(candidate)
        connection.execute(projects.update().where(projects.c.id == row.id).values(key=candidate))

    op.alter_column("projects", "key", nullable=False)
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
