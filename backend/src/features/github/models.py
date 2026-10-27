import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class GitHubInstallation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Instalação do GitHub App ligada a um workspace (M10, ADR-068).

    `installation_id` é o id numérico do GitHub, único entre as linhas ativas: uma
    instalação pertence a no máximo um workspace. É isso que torna inequívoco o
    `FD-123` de um pull request, já que o prefixo `FD` é igual em todos os
    workspaces e o workspace vem da instalação, não do texto do PR.

    `account_type` guarda o valor cru do GitHub (`User`/`Organization`), sem
    `domain_enum`: é só exibição, e um tipo novo do lado do GitHub não deveria
    impedir a conexão.
    """

    __tablename__ = "github_installations"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_login: Mapped[str] = mapped_column(nullable=False)
    account_type: Mapped[str] = mapped_column(nullable=False)
    connected_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


Index(
    "uq_github_installations_installation_id_active",
    GitHubInstallation.installation_id,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
Index("ix_github_installations_workspace_id", GitHubInstallation.workspace_id)
