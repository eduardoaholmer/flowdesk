import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum

if TYPE_CHECKING:
    from src.features.issues.models import Issue


class ProjectStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Project(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Agrupamento de issues acima do time — RF-PROJ-01.

    `status` modela só o ciclo de vida administrativo (visível/arquivado), não
    progresso de execução — isso pertence a um workflow por Issue, fora de
    escopo aqui. Redefinido na Sprint 6 (ACTIVE/ARCHIVED) a partir do placeholder
    especulativo de 4 valores modelado na Sprint 2 (PLANNED/IN_PROGRESS/
    COMPLETED/CANCELED): a tabela nunca teve linha em produção e o contrato de
    negócio desta sprint pede exatamente arquivar/restaurar — ver ADR em
    `docs/09-decision-log.md`.

    `target_date`/`lead_id` vêm do modelo original da Sprint 2 e são mantidos
    (nenhuma regra de negócio desta sprint os usa ainda) para não descartar
    campo já modelado sem necessidade — ficam prontos para Cycles/Dashboard.

    Sem join com `Team` ainda: um projeto hoje é apenas workspace-scoped, não
    atrelado a times específicos (isso chega junto do join `project_teams`,
    deixado fora por ora).
    """

    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_id_deleted_at", "workspace_id", "deleted_at"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False)
    key: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    icon: Mapped[str | None] = mapped_column(default=None)
    color: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[ProjectStatus] = mapped_column(
        domain_enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE
    )
    target_date: Mapped[date | None] = mapped_column(default=None)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), default=None
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    issues: Mapped[list["Issue"]] = relationship(back_populates="project")


Index(
    "uq_projects_workspace_id_slug_active",
    Project.workspace_id,
    Project.slug,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)

Index(
    "uq_projects_workspace_id_name_active",
    Project.workspace_id,
    func.lower(Project.name),
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)

Index(
    "uq_projects_workspace_id_key_active",
    Project.workspace_id,
    Project.key,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class ProjectMember(UUIDPrimaryKeyMixin, Base):
    """Associação informativa de um usuário a um projeto (RF-PROJ-06) — NÃO é
    mecanismo de controle de acesso. A única camada de autorização do sistema
    continua sendo o RBAC de workspace (`core/authorization.py`); pertencer a um
    projeto não concede nem nega nenhuma permissão, só alimenta a UI (avatares,
    "meus projetos"). Ver ADR-049 em `docs/09-decision-log.md`.

    Sem soft delete: membership é adicionada/removida, nunca arquivada — ao
    contrário de `Project`/`Label`, "remover do projeto" não tem histórico a
    preservar (o evento fica em `ProjectActivityLog`). Sem `updated_at` pela
    mesma razão (a linha nunca é atualizada in-place, só criada/apagada).
    """

    __tablename__ = "project_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


Index(
    "uq_project_members_project_id_user_id",
    ProjectMember.project_id,
    ProjectMember.user_id,
    unique=True,
)


class ProjectActivityLog(UUIDPrimaryKeyMixin, Base):
    """Auditoria de eventos de projeto (criação, atualização, arquivamento,
    restauração, exclusão) — append-only, sem `updated_at`, sem soft delete,
    mesmo racional de `WorkspaceActivityLog` (`features/workspaces/models.py`).

    Tabela própria em vez de reaproveitar `activity_logs` (histórico de diff de
    campo de uma `Issue`) ou `workspace_activity_logs` (payload sem `project_id`
    dedicado): cada log de auditoria deste sistema é modelado para o agregado
    que audita, não generalizado em uma tabela polimórfica — ver ADR-009 em
    `docs/09-decision-log.md`.
    """

    __tablename__ = "project_activity_logs"
    __table_args__ = (
        Index("ix_project_activity_logs_project_id_created_at", "project_id", "created_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(nullable=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
