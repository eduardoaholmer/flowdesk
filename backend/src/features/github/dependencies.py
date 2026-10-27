from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import PermissionService, get_permission_service
from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.redis_client import get_redis
from src.features.github.client import GitHubAppClient, GitHubAppClientProtocol
from src.features.github.repository import (
    GitHubConnectStateRepository,
    GitHubConnectStateRepositoryProtocol,
    GitHubInstallationRepository,
    GitHubInstallationRepositoryProtocol,
)
from src.features.github.service import GitHubIntegrationService
from src.features.permissions.dependencies import get_permission_override_repository
from src.features.permissions.repository import PermissionOverrideRepositoryProtocol
from src.features.workspaces.dependencies import get_workspace_repository
from src.features.workspaces.repository import WorkspaceRepositoryProtocol


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
