import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum
from src.features.auth.models import User
from src.features.labels.models import Label
from src.features.projects.models import Project
from src.features.workflow_states.models import WorkflowState

if TYPE_CHECKING:
    from src.features.comments.models import Comment

_IDENTIFIER_PREFIX = "FD"


class IssuePriority(enum.StrEnum):
    NO_PRIORITY = "NO_PRIORITY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Issue(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """`number` é único por workspace e **nunca reciclado**, mesmo após soft
    delete — ao contrário de slug/key/name (únicos parciais em
    `deleted_at IS NULL`), reaproveitar o número faria `FD-123` apontar para
    duas issues diferentes ao longo do tempo (mesmo racional de
    docs/03-database.md §8, agora escopado a workspace em vez de time).

    `identifier` (`FD-{number}`) é derivado, não persistido — `CLAUDE.md` §3
    permite comportamento trivial derivado de dado em um model via `@property`.

    `version` sustenta concorrência otimista (docs/03-database.md §3): o
    cliente envia a versão que possuía ao editar; um UPDATE que não bate a
    versão afeta zero linhas e o service traduz isso em `IssueVersionConflictError`,
    nunca "last write wins".

    `parent_id` (Sprint 9.4, ADR-059) modela sub-issues — auto-referência
    nullable, sem `relationship()` ORM (nenhum consumidor precisa de
    eager-load de pai/filhos, só filtrar por `parent_id` via repository).
    Limitado a um único nível: `IssueService` recusa vincular uma issue que já
    é pai (tem filhos) ou que já é filha (tem `parent_id`) — ver
    `IssueService._validate_parent_link`.
    """

    __tablename__ = "issues"
    __table_args__ = (
        Index(
            "ix_issues_workspace_id_status_id_deleted_at",
            "workspace_id",
            "status_id",
            "deleted_at",
        ),
        Index(
            "ix_issues_workspace_id_deleted_at_updated_at",
            "workspace_id",
            "deleted_at",
            text("updated_at DESC"),
        ),
        Index("ix_issues_assignee_id_deleted_at", "assignee_id", "deleted_at"),
        Index("ix_issues_creator_id_deleted_at", "creator_id", "deleted_at"),
        Index("ix_issues_project_id_deleted_at", "project_id", "deleted_at"),
        Index("ix_issues_parent_id_deleted_at", "parent_id", "deleted_at"),
        Index(
            "ix_issues_title_description_fts",
            text("to_tsvector('simple', title || ' ' || coalesce(description, ''))"),
            postgresql_using="gin",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), default=None
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("issues.id", ondelete="RESTRICT"), default=None
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
    estimate: Mapped[int | None] = mapped_column(default=None)
    due_date: Mapped[date | None] = mapped_column(Date(), default=None)
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    project: Mapped[Project | None] = relationship(back_populates="issues")
    workflow_state: Mapped[WorkflowState] = relationship()
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    label_links: Mapped[list["IssueLabel"]] = relationship(
        back_populates="issue", passive_deletes=True
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="issue")
    comments: Mapped[list["Comment"]] = relationship(back_populates="issue")

    @property
    def identifier(self) -> str:
        return f"{_IDENTIFIER_PREFIX}-{self.number}"


Index(
    "uq_issues_workspace_id_number",
    Issue.workspace_id,
    Issue.number,
    unique=True,
)


class WorkspaceIssueCounter(TimestampMixin, Base):
    """Contador de número sequencial de issue por workspace. Ao contrário de
    `TeamIssueCounter` (`features/teams/models.py`), a linha não é pré-criada
    por nenhum evento de ciclo de vida (não há gancho em `WorkspaceService`
    para isso nesta sprint) — `IssueRepository.next_number()` a cria sob
    demanda via `INSERT ... ON CONFLICT DO UPDATE` (ver ADR-012, Decisão 3).
    """

    __tablename__ = "workspace_issue_counters"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), primary_key=True
    )
    next_number: Mapped[int] = mapped_column(nullable=False, default=1)


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
