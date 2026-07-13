import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum
from src.features.auth.models import User
from src.features.labels.models import Label
from src.features.projects.models import Project
from src.features.teams.models import Team, WorkflowState

if TYPE_CHECKING:
    from src.features.comments.models import Comment


class IssuePriority(enum.StrEnum):
    NO_PRIORITY = "NO_PRIORITY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Issue(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """`number` é único por time e **nunca reciclado**, mesmo após soft delete — ao
    contrário de slug/key/name (únicos parciais em `deleted_at IS NULL`), reaproveitar
    o número faria `ENG-123` apontar para duas issues diferentes ao longo do tempo.

    `version` sustenta concorrência otimista (docs/03-database.md §3): o cliente envia
    a versão que possuía ao editar; um UPDATE que não bate a versão afeta zero linhas
    e o service (Sprint 3+) traduz isso em ConflictError, nunca "last write wins".
    """

    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_team_id_status_id_deleted_at", "team_id", "status_id", "deleted_at"),
        Index(
            "ix_issues_workspace_id_deleted_at_updated_at",
            "workspace_id",
            "deleted_at",
            text("updated_at DESC"),
        ),
        Index("ix_issues_assignee_id_deleted_at", "assignee_id", "deleted_at"),
        Index(
            "ix_issues_title_description_fts",
            text("to_tsvector('simple', title || ' ' || coalesce(description, ''))"),
            postgresql_using="gin",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), default=None
    )
    number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    status_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_states.id", ondelete="RESTRICT"), nullable=False
    )
    priority: Mapped[IssuePriority] = mapped_column(
        domain_enum(IssuePriority), nullable=False, default=IssuePriority.NO_PRIORITY
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), default=None
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    team: Mapped[Team] = relationship()
    project: Mapped[Project | None] = relationship(back_populates="issues")
    status: Mapped[WorkflowState] = relationship()
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    label_links: Mapped[list["IssueLabel"]] = relationship(
        back_populates="issue", passive_deletes=True
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="issue")
    comments: Mapped[list["Comment"]] = relationship(back_populates="issue")


Index(
    "uq_issues_team_id_number",
    Issue.team_id,
    Issue.number,
    unique=True,
)


class IssueLabel(Base):
    """Associação pura N:N — modelada como classe explícita (não `Table` solta) para
    deixar espaço a metadado futuro sem exigir converter uma Table em entidade depois.
    """

    __tablename__ = "issue_labels"

    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped[Issue] = relationship(back_populates="label_links")
    label: Mapped[Label] = relationship(back_populates="issue_links")


class ActivityLog(UUIDPrimaryKeyMixin, Base):
    """Append-only por natureza (auditoria) — sem `updated_at`, sem soft delete.
    "Excluir" um log de auditoria contradiria seu propósito (docs/03-database.md §2).
    """

    __tablename__ = "activity_logs"
    __table_args__ = (Index("ix_activity_logs_issue_id_created_at", "issue_id", "created_at"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(nullable=False)
    field: Mapped[str | None] = mapped_column(default=None)
    old_value: Mapped[str | None] = mapped_column(default=None)
    new_value: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped[Issue] = relationship(back_populates="activity_logs")
