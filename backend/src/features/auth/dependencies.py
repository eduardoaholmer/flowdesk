from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.dependencies import get_session_repository, get_user_repository
from src.core.mail import LoggingMailSender, get_mail_sender
from src.features.auth.repository import (
    PasswordResetRepository,
    PasswordResetRepositoryProtocol,
    SessionRepositoryProtocol,
    UserRepositoryProtocol,
)
from src.features.auth.service import AuthService


def get_password_reset_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PasswordResetRepository:
    return PasswordResetRepository(session)


def get_auth_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    session_repo: SessionRepositoryProtocol = Depends(get_session_repository),
    settings: Settings = Depends(get_settings),
    password_reset_repo: PasswordResetRepositoryProtocol = Depends(get_password_reset_repository),
    mail_sender: LoggingMailSender = Depends(get_mail_sender),
) -> AuthService:
    return AuthService(user_repo, session_repo, settings, password_reset_repo, mail_sender)
