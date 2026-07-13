import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.auth.models import RefreshToken, Session, User


class UserRepositoryProtocol(Protocol):
    async def create(self, user: User) -> User: ...
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result: User | None = await self._session.scalar(stmt)
        return result

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(), User.deleted_at.is_(None)
        )
        result: User | None = await self._session.scalar(stmt)
        return result


class SessionRepositoryProtocol(Protocol):
    async def create_session(self, session: Session) -> Session: ...
    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken: ...
    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None: ...
    async def revoke_session(self, session_id: uuid.UUID) -> None: ...
    async def list_active_by_user(self, user_id: uuid.UUID) -> Sequence[Session]: ...


class SessionRepository:
    """Gerencia Session + RefreshToken juntos — RefreshToken é filho de Session,
    não um agregado próprio (ver plano da Sprint 2 / CLAUDE.md §6).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, session: Session) -> Session:
        self._session.add(session)
        await self._session.flush()
        return session

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result: RefreshToken | None = await self._session.scalar(stmt)
        return result

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        """Revoga a sessão e, junto, qualquer refresh token ainda ativo dela —
        um logout nunca deve deixar um token utilizável para trás.
        """
        now = datetime.now(UTC)
        await self._session.execute(
            update(Session).where(Session.id == session_id).values(revoked_at=now)
        )
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def list_active_by_user(self, user_id: uuid.UUID) -> Sequence[Session]:
        stmt = select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
        return (await self._session.scalars(stmt)).all()
