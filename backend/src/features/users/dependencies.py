from fastapi import Depends

from src.core.dependencies import get_user_repository
from src.features.auth.repository import UserRepositoryProtocol
from src.features.users.service import UserService


def get_user_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)
