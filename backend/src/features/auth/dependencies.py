from fastapi import Depends

from src.core.config import Settings, get_settings
from src.core.dependencies import get_session_repository, get_user_repository
from src.features.auth.repository import SessionRepositoryProtocol, UserRepositoryProtocol
from src.features.auth.service import AuthService


def get_auth_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    session_repo: SessionRepositoryProtocol = Depends(get_session_repository),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(user_repo, session_repo, settings)
