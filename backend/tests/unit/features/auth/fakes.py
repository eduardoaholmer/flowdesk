import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.auth.models import RefreshToken, Session, User
from uuid6 import uuid7


class FakeUserRepository:
    """Implementa `UserRepositoryProtocol` em memória — permite testar `AuthService`
    sem banco (CLAUDE.md §5/§6). Também simula os defaults que só existem no
    flush do SQLAlchemy real (`id`, `created_at`), já que aqui não há sessão.
    """

    def __init__(self) -> None:
        self.users: dict[uuid.UUID, User] = {}

    async def create(self, user: User) -> User:
        if user.id is None:
            user.id = uuid7()
        if user.created_at is None:
            user.created_at = datetime.now(UTC)
        self.users[user.id] = user
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        user = self.users.get(user_id)
        if user is None or user.deleted_at is not None:
            return None
        return user

    async def get_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email.lower() == email.lower() and user.deleted_at is None:
                return user
        return None


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[uuid.UUID, Session] = {}
        self.refresh_tokens: dict[uuid.UUID, RefreshToken] = {}

    async def create_session(self, session: Session) -> Session:
        if session.id is None:
            session.id = uuid7()
        self.sessions[session.id] = session
        return session

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        if token.id is None:
            token.id = uuid7()
        self.refresh_tokens[token.id] = token
        token.session = self.sessions[token.session_id]
        return token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        for token in self.refresh_tokens.values():
            if token.token_hash == token_hash:
                return token
        return None

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        now = datetime.now(UTC)
        session = self.sessions.get(session_id)
        if session is not None:
            session.revoked_at = now
        for token in self.refresh_tokens.values():
            if token.session_id == session_id and token.revoked_at is None:
                token.revoked_at = now

    async def list_active_by_user(self, user_id: uuid.UUID) -> Sequence[Session]:
        return [s for s in self.sessions.values() if s.user_id == user_id and s.revoked_at is None]

    async def revoke_refresh_token(
        self, token_id: uuid.UUID, *, replaced_by_id: uuid.UUID | None = None
    ) -> None:
        token = self.refresh_tokens.get(token_id)
        if token is not None:
            token.revoked_at = datetime.now(UTC)
            token.replaced_by_id = replaced_by_id
