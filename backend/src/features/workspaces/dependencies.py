from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.dependencies import get_user_repository
from src.features.auth.repository import UserRepositoryProtocol
from src.features.workspaces.repository import (
    InvitationRepository,
    InvitationRepositoryProtocol,
    WorkspaceRepository,
    WorkspaceRepositoryProtocol,
)
from src.features.workspaces.service import InvitationService, WorkspaceService


def get_workspace_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def get_invitation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> InvitationRepository:
    return InvitationRepository(session)


def get_workspace_service(
    workspace_repo: WorkspaceRepositoryProtocol = Depends(get_workspace_repository),
) -> WorkspaceService:
    return WorkspaceService(workspace_repo)


def get_invitation_service(
    invitation_repo: InvitationRepositoryProtocol = Depends(get_invitation_repository),
    workspace_repo: WorkspaceRepositoryProtocol = Depends(get_workspace_repository),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> InvitationService:
    return InvitationService(invitation_repo, workspace_repo, user_repo, settings)
