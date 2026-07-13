import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum
from src.features.auth.models import User


class WorkspaceRole(enum.StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class Workspace(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """`owner_id` é um ponteiro de conveniência (criador original).

    A fonte de verdade de "quem é OWNER hoje" é `WorkspaceMember.role` — uma
    transferência de propriedade (fora de escopo desta sprint) muda o membro,
    não necessariamente este campo. Nenhuma FK garante essa consistência; é
    responsabilidade do service (Sprint 3+) manter as duas em sincronia.
    """

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    members: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace")
    invitations: Mapped[list["Invitation"]] = relationship(back_populates="workspace")


Index(
    "uq_workspaces_slug_active",
    Workspace.slug,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class WorkspaceMember(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        Index("ix_workspace_members_user_id", "user_id"),
        Index("ix_workspace_members_workspace_id_deleted_at", "workspace_id", "deleted_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[WorkspaceRole] = mapped_column(domain_enum(WorkspaceRole), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


Index(
    "uq_workspace_members_workspace_id_user_id_active",
    WorkspaceMember.workspace_id,
    WorkspaceMember.user_id,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class Invitation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Soft delete permite a um OWNER/ADMIN cancelar um convite pendente sem apagar
    o histórico de quem convidou quem — mesma lógica já aplicada ao resto do domínio
    (ver ADR em docs/09-decision-log.md, esta não estava no ER original da Sprint 0).
    """

    __tablename__ = "invitations"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    email: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[WorkspaceRole] = mapped_column(domain_enum(WorkspaceRole), nullable=False)
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    workspace: Mapped[Workspace] = relationship(back_populates="invitations")


Index(
    "uq_invitations_workspace_id_email_pending",
    Invitation.workspace_id,
    Invitation.email,
    unique=True,
    postgresql_where=text("accepted_at IS NULL AND deleted_at IS NULL"),
)
