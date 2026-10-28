"""add actor_source to activity_logs

Revision ID: b1ec8ae65958
Revises: 5f80ea552189
Create Date: 2026-10-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1ec8ae65958"
down_revision: str | None = "5f80ea552189"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Aditiva: toda linha existente foi feita por uma pessoa, então o default
    # `USER` já é o valor correto e nenhum `actor_id` muda.
    op.add_column(
        "activity_logs",
        sa.Column(
            "actor_source",
            sa.Enum("USER", "GITHUB", name="activityactorsource", native_enum=False, length=32),
            server_default="USER",
            nullable=False,
        ),
    )
    op.alter_column("activity_logs", "actor_id", existing_type=sa.Uuid(), nullable=True)
    op.create_check_constraint(
        "ck_activity_logs_user_actor_required",
        "activity_logs",
        "actor_source <> 'USER' OR actor_id IS NOT NULL",
    )


def downgrade() -> None:
    # Volta a exigir autor: atividade de automação sem membro correspondente não
    # tem como ser representada no schema antigo e é descartada.
    op.execute("DELETE FROM activity_logs WHERE actor_id IS NULL")
    op.drop_constraint("ck_activity_logs_user_actor_required", "activity_logs", type_="check")
    op.alter_column("activity_logs", "actor_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_column("activity_logs", "actor_source")
