from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.exceptions import InvalidTokenError
from src.core.security import CurrentUser, decode_access_token
from src.features.auth.repository import SessionRepository, UserRepository, UserRepositoryProtocol

_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


def get_session_repository(session: AsyncSession = Depends(get_db_session)) -> SessionRepository:
    return SessionRepository(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Resolve o usuário autenticado a partir do header `Authorization: Bearer`.

    Qualquer falha (header ausente, token malformado/expirado, usuário
    inexistente ou desativado/soft-deleted) colapsa no mesmo `InvalidTokenError`
    — ver `docs/07-security.md` §10 e ADR-008 sobre por que não diferenciamos
    essas causas na resposta ao cliente.
    """
    if credentials is None:
        raise InvalidTokenError()

    claims = decode_access_token(credentials.credentials, settings)
    user = await user_repo.get_by_id(claims.sub)
    if user is None:
        raise InvalidTokenError()

    return CurrentUser(id=user.id, email=user.email, name=user.name)
