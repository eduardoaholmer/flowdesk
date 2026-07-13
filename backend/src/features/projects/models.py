import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum

if TYPE_CHECKING:
    from src.features.issues.models import Issue


class ProjectStatus(enum.StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class Project(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Agrupamento de issues acima do time — RF-PROJ-01, pós-MVP como feature, mas o
    schema é modelado agora (pedido explícito do usuário nesta sprint). Sem join com
    `Team` ainda: um projeto hoje é apenas workspace-scoped, não atrelado a times
    específicos (isso chega junto do join `project_teams`, deixado fora por ora).
    """

    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_id_deleted_at", "workspace_id", "deleted_at"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[ProjectStatus] = mapped_column(
        domain_enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNED
    )
    target_date: Mapped[date | None] = mapped_column(default=None)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), default=None
    )

    issues: Mapped[list["Issue"]] = relationship(back_populates="project")
