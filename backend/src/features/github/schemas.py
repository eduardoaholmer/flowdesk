import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError

from src.features.github.exceptions import GitHubWebhookPayloadInvalidError
from src.features.github.models import (
    GITHUB_DELIVERY_ID_MAX_LENGTH,
    GitHubAutomationEvent,
    GitHubInstallation,
    GitHubPullRequestState,
    GitHubWebhookOutcome,
)

# Nome de evento do GitHub (`pull_request`, `installation_repositories`...) — curto
# por natureza; o teto só impede um cabeçalho arbitrariamente grande na coluna.
_EVENT_NAME_MAX_LENGTH = 64
PULL_REQUEST_EVENT = "pull_request"


@dataclass(frozen=True)
class GitHubIntegrationStatus:
    configured: bool
    installations: Sequence[GitHubInstallation]


@dataclass(frozen=True)
class GitHubConnectionStart:
    install_url: str
    state: str


class GitHubInstallationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    installation_id: int
    account_login: str
    account_type: str
    connected_by_id: uuid.UUID
    suspended_at: datetime | None
    created_at: datetime


class GitHubIntegrationResponse(BaseModel):
    configured: bool
    installations: list[GitHubInstallationResponse]

    @classmethod
    def from_status(cls, status: GitHubIntegrationStatus) -> "GitHubIntegrationResponse":
        return cls(
            configured=status.configured,
            installations=[
                GitHubInstallationResponse.model_validate(installation)
                for installation in status.installations
            ],
        )


class GitHubConnectResponse(BaseModel):
    install_url: str


class GitHubWebhookInstallationRef(BaseModel):
    id: int
    suspended_at: datetime | None = None


class GitHubAccountRef(BaseModel):
    login: str


class GitHubSenderRef(BaseModel):
    id: int
    login: str


class GitHubBranchRef(BaseModel):
    ref: str


class GitHubRepositoryRef(BaseModel):
    full_name: str


class GitHubPullRequestPayload(BaseModel):
    id: int
    number: int
    title: str
    body: str | None = None
    html_url: str
    state: str
    draft: bool = False
    merged: bool | None = None
    user: GitHubAccountRef
    head: GitHubBranchRef
    updated_at: datetime

    @property
    def flowdesk_state(self) -> GitHubPullRequestState:
        if self.merged:
            return GitHubPullRequestState.MERGED
        if self.state == "closed":
            return GitHubPullRequestState.CLOSED
        if self.draft:
            return GitHubPullRequestState.DRAFT
        return GitHubPullRequestState.OPEN


class GitHubWebhookPayload(BaseModel):
    """Só o que o FlowDesk lê do corpo dos eventos tratados. Campos extras são
    ignorados (o default do Pydantic): cada evento do GitHub traz dezenas de campos
    que não interessam, e o formato completo é do GitHub, não nosso."""

    action: str | None = None
    installation: GitHubWebhookInstallationRef | None = None


class GitHubPullRequestEventPayload(GitHubWebhookPayload):
    """Formato exigido só quando `X-GitHub-Event` é `pull_request`. Outros eventos que
    também trazem um `pull_request` (`pull_request_review`, por exemplo) não passam
    por aqui: o FlowDesk os ignora, e um formato diferente neles não pode virar 422."""

    pull_request: GitHubPullRequestPayload
    repository: GitHubRepositoryRef
    sender: GitHubSenderRef | None = None


@dataclass(frozen=True)
class GitHubWebhookDeliveryInput:
    delivery_id: str
    event: str
    payload: GitHubWebhookPayload

    @classmethod
    def parse(
        cls, *, delivery_id: str | None, event: str | None, body: bytes
    ) -> "GitHubWebhookDeliveryInput":
        """Chamado só depois de a assinatura ser validada (`verify_github_webhook`)."""
        if (
            not delivery_id
            or len(delivery_id) > GITHUB_DELIVERY_ID_MAX_LENGTH
            or not event
            or len(event) > _EVENT_NAME_MAX_LENGTH
        ):
            raise GitHubWebhookPayloadInvalidError()
        payload_model = (
            GitHubPullRequestEventPayload if event == PULL_REQUEST_EVENT else GitHubWebhookPayload
        )
        try:
            payload = payload_model.model_validate_json(body)
        except PydanticValidationError as exc:
            raise GitHubWebhookPayloadInvalidError() from exc
        return cls(delivery_id=delivery_id, event=event, payload=payload)


@dataclass(frozen=True)
class GitHubWebhookResult:
    outcome: GitHubWebhookOutcome
    duplicate: bool


class GitHubWebhookResponse(BaseModel):
    outcome: GitHubWebhookOutcome
    duplicate: bool


class GitHubPullRequestLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_full_name: str
    pr_number: int
    pr_url: str
    pr_title: str
    pr_state: GitHubPullRequestState
    author_login: str
    head_branch: str
    pr_updated_at: datetime


@dataclass(frozen=True)
class GitHubStatusAutomationView:
    event: GitHubAutomationEvent
    target_state_id: uuid.UUID | None


class GitHubStatusAutomationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: GitHubAutomationEvent
    target_state_id: uuid.UUID | None


class GitHubStatusAutomationUpdateRequest(BaseModel):
    event: GitHubAutomationEvent
    target_state_id: uuid.UUID | None
