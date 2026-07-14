import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.features.issues.models import IssueLabel


class Label(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "labels"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    color: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)

    issue_links: Mapped[list["IssueLabel"]] = relationship(
        back_populates="label", passive_deletes=True
    )


Index(
    "uq_labels_workspace_id_name_active",
    Label.workspace_id,
    Label.name,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class LabelActivityLog(UUIDPrimaryKeyMixin, Base):
    """Auditoria de eventos do próprio Label (criação, atualização, exclusão) —
    append-only, sem `updated_at`, sem soft delete, mesmo padrão de
    `ProjectActivityLog`/`WorkspaceActivityLog` (`metadata JSONB`, ver ADR-009).

    Tabela própria em vez de reaproveitar `ActivityLog` (`features/issues/models.py`,
    `issue_id` obrigatório): eventos de ciclo de vida de um Label (workspace-scoped,
    não issue-scoped) não têm `issue_id` — só quando um Label é *aplicado/removido
    de uma Issue* é que o evento pertence à timeline da Issue (`ActivityLog`,
    ações `label.added`/`label.removed`, ver `features/issues/service.py`).
    """

    __tablename__ = "label_activity_logs"
    __table_args__ = (
        Index("ix_label_activity_logs_label_id_created_at", "label_id", "created_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labels.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(nullable=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
