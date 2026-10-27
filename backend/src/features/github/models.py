import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum

# `X-GitHub-Delivery` é um GUID (36 caracteres); a folga cobre variações de formato
# sem aceitar um valor arbitrariamente grande vindo de um cabeçalho.
GITHUB_DELIVERY_ID_MAX_LENGTH = 64


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


class GitHubWebhookOutcome(enum.StrEnum):
    PROCESSED = "PROCESSED"
    IGNORED = "IGNORED"


class GitHubWebhookDelivery(Base):
    """Uma entrega recebida em `POST /webhooks/github` (Sprint 10.2, ADR-069).

    `delivery_id` (o `X-GitHub-Delivery`) é a chave primária: o GitHub reenvia uma
    entrega com o mesmo id, e a linha é gravada na mesma transação do efeito, então
    um reenvio nunca aplica o efeito duas vezes. Também é a trilha para responder
    "o GitHub mandou e o FlowDesk ignorou por quê?" (`reason`).

    Append-only, como `ActivityLog`: sem `updated_at` nem soft delete. A retenção
    (expurgo depois de 30 dias) é operacional, pelo runbook — por isso o índice em
    `received_at`. `workspace_id` só é preenchido quando a instalação do evento é
    conhecida; uma entrega de instalação desconhecida não pertence a nenhum tenant.
    """

    __tablename__ = "github_webhook_deliveries"

    delivery_id: Mapped[str] = mapped_column(
        String(GITHUB_DELIVERY_ID_MAX_LENGTH), primary_key=True
    )
    event: Mapped[str] = mapped_column(nullable=False)
    action: Mapped[str | None] = mapped_column(default=None)
    installation_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), default=None
    )
    outcome: Mapped[GitHubWebhookOutcome] = mapped_column(
        domain_enum(GitHubWebhookOutcome), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(default=None)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


Index("ix_github_webhook_deliveries_received_at", GitHubWebhookDelivery.received_at)


class GitHubPullRequestState(enum.StrEnum):
    OPEN = "OPEN"
    DRAFT = "DRAFT"
    MERGED = "MERGED"
    CLOSED = "CLOSED"


class GitHubPullRequestLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Vínculo entre uma issue e um pull request que cita o identificador dela
    (`FD-123`) na branch, no título ou no corpo (Sprint 10.3, ADR-070).

    A identidade do PR é `pull_request_id`, o id global do GitHub, e não
    `repository_full_name` + número: renomear ou transferir o repositório muda o
    nome, e o vínculo duplicaria. Nome do repositório, título, estado, autor e branch
    são cópias atualizadas a cada evento, para a UI não precisar chamar o GitHub.

    Sem soft delete, como `issue_labels`: um PR que deixa de citar a issue some da
    lista, e não há histórico a preservar além do que o próprio GitHub guarda.
    `pr_updated_at` é o `updated_at` do PR no último evento aplicado — entregas
    chegam fora de ordem, e um evento mais antigo não pode sobrescrever um mais novo.
    """

    __tablename__ = "issue_github_links"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False
    )
    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pull_request_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repository_full_name: Mapped[str] = mapped_column(nullable=False)
    pr_number: Mapped[int] = mapped_column(nullable=False)
    pr_url: Mapped[str] = mapped_column(nullable=False)
    pr_title: Mapped[str] = mapped_column(nullable=False)
    pr_state: Mapped[GitHubPullRequestState] = mapped_column(
        domain_enum(GitHubPullRequestState), nullable=False
    )
    author_login: Mapped[str] = mapped_column(nullable=False)
    head_branch: Mapped[str] = mapped_column(nullable=False)
    pr_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index(
    "uq_issue_github_links_issue_id_pull_request_id",
    GitHubPullRequestLink.issue_id,
    GitHubPullRequestLink.pull_request_id,
    unique=True,
)
Index(
    "ix_issue_github_links_workspace_id_pull_request_id",
    GitHubPullRequestLink.workspace_id,
    GitHubPullRequestLink.pull_request_id,
)
