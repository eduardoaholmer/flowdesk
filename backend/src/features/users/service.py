import uuid

from src.core.exceptions import NotFoundError
from src.features.auth.models import User
from src.features.auth.repository import UserRepositoryProtocol


class UserService:
    def __init__(self, user_repo: UserRepositoryProtocol) -> None:
        self._user_repo = user_repo

    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError()
        return user
