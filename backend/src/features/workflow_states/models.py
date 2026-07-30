import enum
import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum


class WorkflowStateCategory(enum.StrEnum):
    """Categoria semântica do status, independente do `name` (livremente
    editável pelo usuário) — permite a consumidores que precisam saber "isto
    conta como concluído/cancelado" (ex.: `ProjectRepository.issue_counts`,
    barra de progresso) não acoplar a uma string de nome customizável.
    """

    BACKLOG = "BACKLOG"
    UNSTARTED = "UNSTARTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class WorkflowState(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Status de issue customizável por workspace (Sprint 9.2, ADR-056 reabre a
    ADR-035). Reaproveita a tabela `workflow_states`, dormente desde a Sprint 2
    em escopo de time (`Team`, nunca reativado) — agora escopada diretamente a
    `workspace_id`, sem reviver `Team`/membership.

    `position` ordena as colunas do board; `is_default` marca o status
    atribuído a uma issue nova quando o cliente não informa um explicitamente.
    Exclusão de um status com issues vinculadas é bloqueada em nível de
    aplicação (`WorkflowStateHasIssuesError`) até o chamador informar para
    onde reatribuí-las — ver `service.py`.
    """

    __tablename__ = "workflow_states"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[WorkflowStateCategory] = mapped_column(
        domain_enum(WorkflowStateCategory), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)


Index(
    "uq_workflow_states_workspace_id_name_active",
    WorkflowState.workspace_id,
    WorkflowState.name,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
Index(
    "uq_workflow_states_workspace_id_position_active",
    WorkflowState.workspace_id,
    WorkflowState.position,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
Index(
    "uq_workflow_states_workspace_id_default_active",
    WorkflowState.workspace_id,
    unique=True,
    postgresql_where=text("is_default AND deleted_at IS NULL"),
)
