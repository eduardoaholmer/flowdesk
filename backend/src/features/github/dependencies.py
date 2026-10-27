from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import PermissionService, get_permission_service
from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.logging import get_logger
from src.core.redis_client import get_redis
from src.features.github.client import GitHubAppClient, GitHubAppClientProtocol
from src.features.github.exceptions import (
    GitHubWebhookPayloadTooLargeError,
    GitHubWebhookSignatureInvalidError,
)
from src.features.github.models import GITHUB_DELIVERY_ID_MAX_LENGTH
from src.features.github.repository import (
    GitHubConnectStateRepository,
    GitHubConnectStateRepositoryProtocol,
    GitHubInstallationRepository,
    GitHubInstallationRepositoryProtocol,
    GitHubPullRequestLinkRepository,
    GitHubPullRequestLinkRepositoryProtocol,
    GitHubWebhookDeliveryRepository,
    GitHubWebhookDeliveryRepositoryProtocol,
)
from src.features.github.service import (
    GitHubIntegrationService,
    GitHubPullRequestLinkService,
    GitHubWebhookService,
)
from src.features.github.signature import is_valid_webhook_signature
from src.features.issues.repository import IssueRepository, IssueRepositoryProtocol
from src.features.permissions.dependencies import get_permission_override_repository
from src.features.permissions.repository import PermissionOverrideRepositoryProtocol
from src.features.workspaces.dependencies import get_workspace_repository
from src.features.workspaces.repository import WorkspaceRepositoryProtocol

logger = get_logger(__name__)

SIGNATURE_HEADER = "X-Hub-Signature-256"
DELIVERY_HEADER = "X-GitHub-Delivery"
EVENT_HEADER = "X-GitHub-Event"


def get_github_installation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> GitHubInstallationRepository:
    return GitHubInstallationRepository(session)


async def get_github_connect_state_repository() -> GitHubConnectStateRepository:
    # `async` de propósito: dependência síncrona roda numa thread do pool, sem o
    # event loop que `get_redis` usa para escolher o cliente.
    return GitHubConnectStateRepository(get_redis())


def get_github_app_client(
    settings: Settings = Depends(get_settings),
) -> GitHubAppClientProtocol | None:
    if not settings.github_app_configured:
        return None
    # `_require_full_github_app_config` garante os três campos juntos.
    assert settings.github_app_client_id is not None
    assert settings.github_app_client_secret is not None
    assert settings.github_app_slug is not None
    return GitHubAppClient(
        slug=settings.github_app_slug,
        client_id=settings.github_app_client_id,
        client_secret=settings.github_app_client_secret,
    )


def get_github_integration_service(
    installation_repo: GitHubInstallationRepositoryProtocol = Depends(
        get_github_installation_repository
    ),
    state_repo: GitHubConnectStateRepositoryProtocol = Depends(get_github_connect_state_repository),
    workspace_repo: WorkspaceRepositoryProtocol = Depends(get_workspace_repository),
    override_repo: PermissionOverrideRepositoryProtocol = Depends(
        get_permission_override_repository
    ),
    permission_service: PermissionService = Depends(get_permission_service),
    client: GitHubAppClientProtocol | None = Depends(get_github_app_client),
) -> GitHubIntegrationService:
    return GitHubIntegrationService(
        installation_repo,
        state_repo,
        workspace_repo,
        override_repo,
        permission_service,
        client,
    )


def get_github_webhook_delivery_repository(
    session: AsyncSession = Depends(get_db_session),
) -> GitHubWebhookDeliveryRepository:
    return GitHubWebhookDeliveryRepository(session)


def get_github_pull_request_link_repository(
    session: AsyncSession = Depends(get_db_session),
) -> GitHubPullRequestLinkRepository:
    return GitHubPullRequestLinkRepository(session)


def get_github_issue_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IssueRepository:
    return IssueRepository(session)


def get_github_webhook_service(
    installation_repo: GitHubInstallationRepositoryProtocol = Depends(
        get_github_installation_repository
    ),
    delivery_repo: GitHubWebhookDeliveryRepositoryProtocol = Depends(
        get_github_webhook_delivery_repository
    ),
    link_repo: GitHubPullRequestLinkRepositoryProtocol = Depends(
        get_github_pull_request_link_repository
    ),
    issue_repo: IssueRepositoryProtocol = Depends(get_github_issue_repository),
) -> GitHubWebhookService:
    return GitHubWebhookService(installation_repo, delivery_repo, link_repo, issue_repo)


def get_github_pull_request_link_service(
    link_repo: GitHubPullRequestLinkRepositoryProtocol = Depends(
        get_github_pull_request_link_repository
    ),
    issue_repo: IssueRepositoryProtocol = Depends(get_github_issue_repository),
) -> GitHubPullRequestLinkService:
    return GitHubPullRequestLinkService(link_repo, issue_repo)


async def verify_github_webhook(
    request: Request, settings: Settings = Depends(get_settings)
) -> bytes:
    """Autenticação de `POST /webhooks/github` (ADR-069): no lugar de JWT e
    `require_permission`, o HMAC do corpo com `GITHUB_WEBHOOK_SECRET`. Devolve o
    corpo bruto já verificado; nada do corpo é lido como JSON antes disso.

    O limite de tamanho vem antes do HMAC, e a leitura é por streaming: um corpo
    grande demais é recusado sem ser carregado inteiro na memória."""
    body = await _read_body_with_limit(request, settings.github_webhook_max_body_bytes)
    secret = settings.github_webhook_secret
    if secret is None:
        logger.warning("github_webhook_secret_not_configured")
        raise GitHubWebhookSignatureInvalidError()
    if not is_valid_webhook_signature(secret, body, request.headers.get(SIGNATURE_HEADER)):
        logger.warning(
            "github_webhook_signature_invalid",
            delivery_id=(request.headers.get(DELIVERY_HEADER) or "")[
                :GITHUB_DELIVERY_ID_MAX_LENGTH
            ],
        )
        raise GitHubWebhookSignatureInvalidError()
    return body


async def _read_body_with_limit(request: Request, max_bytes: int) -> bytes:
    declared_length = request.headers.get("content-length")
    if (
        declared_length is not None
        and declared_length.isascii()
        and declared_length.isdigit()
        and int(declared_length) > max_bytes
    ):
        raise GitHubWebhookPayloadTooLargeError()
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > max_bytes:
            raise GitHubWebhookPayloadTooLargeError()
        chunks.append(chunk)
    return b"".join(chunks)
