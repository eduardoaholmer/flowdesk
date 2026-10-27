from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.dependencies import get_session_repository, get_user_repository
from src.core.mail import MailSender, get_mail_sender
from src.features.auth.oauth_providers import (
    GitHubOAuthClient,
    GoogleOAuthClient,
    OAuthClientProtocol,
    OAuthProvider,
)
from src.features.auth.repository import (
    OAuthIdentityRepository,
    OAuthIdentityRepositoryProtocol,
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


def get_oauth_identity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OAuthIdentityRepository:
    return OAuthIdentityRepository(session)


def _build_oauth_clients(settings: Settings) -> dict[OAuthProvider, OAuthClientProtocol]:
    """Só inclui um provedor cujo `client_id` está configurado — a ausência de uma
    entrada aqui é o sinal que `AuthService` usa para responder
    `oauth_provider_not_configured` em vez de tentar chamar um provedor sem
    credenciais (`core/config.py::Settings`)."""
    clients: dict[OAuthProvider, OAuthClientProtocol] = {}
    if settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri:
        clients[OAuthProvider.GOOGLE] = GoogleOAuthClient(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        )
    if settings.github_client_id and settings.github_client_secret and settings.github_redirect_uri:
        clients[OAuthProvider.GITHUB] = GitHubOAuthClient(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
        )
    return clients


def get_auth_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    session_repo: SessionRepositoryProtocol = Depends(get_session_repository),
    settings: Settings = Depends(get_settings),
    password_reset_repo: PasswordResetRepositoryProtocol = Depends(get_password_reset_repository),
    mail_sender: MailSender = Depends(get_mail_sender),
    oauth_identity_repo: OAuthIdentityRepositoryProtocol = Depends(get_oauth_identity_repository),
) -> AuthService:
    return AuthService(
        user_repo,
        session_repo,
        settings,
        password_reset_repo,
        mail_sender,
        oauth_identity_repo,
        _build_oauth_clients(settings),
    )
