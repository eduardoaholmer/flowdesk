"""add storage_provider to attachments

Revision ID: f42ae23f3ec0
Revises: c573b41b553c
Create Date: 2026-07-14 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f42ae23f3ec0"
down_revision: str | None = "c573b41b553c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL direto com server_default (sem expand -> backfill -> contract,
    # docs/03-database.md §10): `attachments` nunca teve linha em produção — a
    # feature existia só como schema+repository desde a Sprint 2, sem service/router
    # até esta sprint (mesma justificativa já usada para `projects.slug`/`created_by`
    # na Sprint 6, ADR-011).
    op.add_column(
        "attachments",
        sa.Column("storage_provider", sa.String(), nullable=False, server_default="local"),
    )
    op.alter_column("attachments", "storage_provider", server_default=None)


def downgrade() -> None:
    op.drop_column("attachments", "storage_provider")
