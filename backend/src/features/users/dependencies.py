from fastapi import Depends

from src.core.dependencies import get_user_repository
from src.features.auth.repository import UserRepositoryProtocol
from src.features.users.service import UserService
from src.features.workspaces.dependencies import get_workspace_repository
from src.features.workspaces.repository import WorkspaceRepositoryProtocol


def get_user_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    workspace_repo: WorkspaceRepositoryProtocol = Depends(get_workspace_repository),
) -> UserService:
    return UserService(user_repo, workspace_repo)
