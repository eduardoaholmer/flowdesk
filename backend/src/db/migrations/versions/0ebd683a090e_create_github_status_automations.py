"""create github_status_automations

Revision ID: 0ebd683a090e
Revises: b1ec8ae65958
Create Date: 2026-10-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0ebd683a090e"
down_revision: str | None = "b1ec8ae65958"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Mesmos defaults de `default_automation_targets` (features/github/service.py),
# resolvidos por workspace pela posição no board. Só para workspaces que já tinham
# uma instalação conectada antes desta migration: os demais recebem os defaults na
# primeira conexão.
_BACKFILL = """
WITH connected AS (
    SELECT DISTINCT workspace_id
    FROM github_installations
    WHERE deleted_at IS NULL
),
ranked AS (
    SELECT
        ws.workspace_id,
        ws.id,
        ws.category,
        row_number() OVER (
            PARTITION BY ws.workspace_id, ws.category ORDER BY ws.position ASC
        ) AS first_rank,
        row_number() OVER (
            PARTITION BY ws.workspace_id, ws.category ORDER BY ws.position DESC
        ) AS last_rank
    FROM workflow_states ws
    JOIN connected c ON c.workspace_id = ws.workspace_id
    WHERE ws.deleted_at IS NULL
),
defaults AS (
    SELECT c.workspace_id, e.event, (
        SELECT r.id FROM ranked r
        WHERE r.workspace_id = c.workspace_id
          AND (
            (e.event = 'PR_DRAFT' AND r.category = 'STARTED' AND r.first_rank = 1)
            OR (e.event = 'PR_OPEN' AND r.category = 'STARTED' AND r.last_rank = 1)
            OR (e.event = 'PR_MERGED' AND r.category = 'COMPLETED' AND r.first_rank = 1)
          )
    ) AS target_state_id
    FROM connected c
    CROSS JOIN (VALUES ('PR_DRAFT'), ('PR_OPEN'), ('PR_MERGED'), ('PR_CLOSED')) AS e(event)
)
INSERT INTO github_status_automations (id, workspace_id, event, target_state_id)
SELECT gen_random_uuid(), workspace_id, event, target_state_id FROM defaults
"""


def upgrade() -> None:
    op.create_table(
        "github_status_automations",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event",
            sa.Enum(
                "PR_DRAFT",
                "PR_OPEN",
                "PR_MERGED",
                "PR_CLOSED",
                name="githubautomationevent",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("target_state_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["target_state_id"], ["workflow_states.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_github_status_automations_workspace_id_event",
        "github_status_automations",
        ["workspace_id", "event"],
        unique=True,
    )
    op.execute(_BACKFILL)


def downgrade() -> None:
    op.drop_index(
        "uq_github_status_automations_workspace_id_event", table_name="github_status_automations"
    )
    op.drop_table("github_status_automations")
