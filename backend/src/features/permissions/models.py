import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.core.permissions import Permission
from src.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum
from src.features.workspaces.models import WorkspaceRole


class PermissionOverride(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Desvio explícito da matriz `ROLE_PERMISSIONS` (`core/authorization.py`)
    para um papel deste workspace (Sprint 9.3, ADR-058 — meio-termo entre RBAC
    fixo e cargos arbitrários: permissões individualmente ligáveis/desligáveis
    dentro de `ADMIN`/`MEMBER`/`GUEST`, nunca `OWNER`).

    Sem soft delete: "resetar para o padrão" é remover a linha (o padrão volta
    a valer), não um estado a preservar — ao contrário de `WorkflowState`, não
    há dado de negócio (issues, contagens) vinculado a uma linha desta tabela.
    `granted=True` concede uma permissão que o papel não teria por padrão;
    `granted=False` revoga uma que ele teria — a ausência de linha é sempre
    "seguir o padrão".
    """

    __tablename__ = "permission_overrides"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[WorkspaceRole] = mapped_column(domain_enum(WorkspaceRole), nullable=False)
    permission: Mapped[Permission] = mapped_column(
        domain_enum(Permission, length=64), nullable=False
    )
    granted: Mapped[bool] = mapped_column(nullable=False)


Index(
    "uq_permission_overrides_workspace_role_permission",
    PermissionOverride.workspace_id,
    PermissionOverride.role,
    PermissionOverride.permission,
    unique=True,
)
