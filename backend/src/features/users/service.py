import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from src.core.exceptions import NotFoundError
from src.features.auth.models import User
from src.features.auth.repository import UserRepositoryProtocol
from src.features.workspaces.models import WorkspaceMember
from src.features.workspaces.repository import WorkspaceRepositoryProtocol


@dataclass(frozen=True)
class UserProfile:
    user: User
    memberships: Sequence[WorkspaceMember]


class UserService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        workspace_repo: WorkspaceRepositoryProtocol,
    ) -> None:
        self._user_repo = user_repo
        self._workspace_repo = workspace_repo

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError()

        memberships = await self._workspace_repo.list_memberships_by_user(user_id)
        return UserProfile(user=user, memberships=memberships)
