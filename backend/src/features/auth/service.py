import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.core.config import Settings
from src.core.logging import get_logger
from src.core.mail import MailSender
from src.core.security import (
    create_access_token,
    generate_password_reset_token,
    generate_refresh_token,
    hash_password,
    hash_password_reset_token,
    hash_refresh_token,
    perform_dummy_verification,
    verify_password,
)
from src.features.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
)
from src.features.auth.models import PasswordResetToken, RefreshToken, Session, User
from src.features.auth.repository import (
    PasswordResetRepositoryProtocol,
    SessionRepositoryProtocol,
    UserRepositoryProtocol,
)
from src.features.auth.schemas import RegisterRequest

logger = get_logger(__name__)


@dataclass(frozen=True)
class LoginResult:
    user: User
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class RefreshResult:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        session_repo: SessionRepositoryProtocol,
        settings: Settings,
        password_reset_repo: PasswordResetRepositoryProtocol,
        mail_sender: MailSender,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._settings = settings
        self._password_reset_repo = password_reset_repo
        self._mail_sender = mail_sender

    async def register(self, payload: RegisterRequest) -> User:
        existing = await self._user_repo.get_by_email(payload.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError()

        user = User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        return await self._user_repo.create(user)

    async def login(
        self,
        email: str,
        password: str,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> LoginResult:
        user = await self._user_repo.get_by_email(email)
        if user is None:
            perform_dummy_verification(password)
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        session = await self._session_repo.create_session(
            Session(user_id=user.id, user_agent=user_agent, ip_address=ip_address)
        )

        refresh_token_plain, _ = await self._issue_refresh_token(session.id)
        access_token = create_access_token(user.id, self._settings)

        return LoginResult(user=user, access_token=access_token, refresh_token=refresh_token_plain)

    async def refresh(self, refresh_token_plain: str) -> RefreshResult:
        token_hash = hash_refresh_token(refresh_token_plain)
        token = await self._session_repo.get_refresh_token_by_hash(token_hash)

        if token is None:
            raise InvalidRefreshTokenError()

        if token.revoked_at is not None:
            # Token já revogado (rotacionado ou sessão deslogada) sendo reapresentado
            # — possível roubo. Revoga toda a sessão como precaução (docs/07-security.md §2).
            logger.warning("refresh_token_reuse_detected", session_id=str(token.session_id))
            await self._session_repo.revoke_session(token.session_id)
            raise InvalidRefreshTokenError()

        if token.expires_at < datetime.now(UTC):
            raise InvalidRefreshTokenError()

        new_refresh_token_plain, new_token = await self._issue_refresh_token(token.session_id)
        await self._session_repo.revoke_refresh_token(token.id, replaced_by_id=new_token.id)

        access_token = create_access_token(token.session.user_id, self._settings)

        return RefreshResult(access_token=access_token, refresh_token=new_refresh_token_plain)

    async def logout(self, refresh_token_plain: str | None) -> None:
        if refresh_token_plain is None:
            return

        token_hash = hash_refresh_token(refresh_token_plain)
        token = await self._session_repo.get_refresh_token_by_hash(token_hash)
        if token is not None:
            await self._session_repo.revoke_session(token.session_id)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        await self._revoke_all_sessions(user_id)

    async def request_password_reset(self, email: str) -> None:
        """Sempre silenciosa quanto à existência do e-mail (anti-enumeration,
        `docs/07-security.md` §10) — o chamador aqui não é confiável do jeito que o
        dono de um workspace convidando alguém é (`WorkspaceService.invite`), então,
        ao contrário do convite, o token nunca é devolvido na resposta.
        """
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return

        await self._password_reset_repo.invalidate_active_for_user(user.id)
        plain = generate_password_reset_token()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self._settings.password_reset_token_expire_minutes
        )
        await self._password_reset_repo.create(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_password_reset_token(plain),
                expires_at=expires_at,
            )
        )
        await self._mail_sender.send_password_reset(email=user.email, token=plain)

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        token_hash = hash_password_reset_token(token)
        reset_token = await self._password_reset_repo.get_by_token_hash(token_hash)

        if reset_token is None:
            raise InvalidPasswordResetTokenError()
        if reset_token.used_at is not None:
            raise InvalidPasswordResetTokenError()
        if reset_token.expires_at < datetime.now(UTC):
            raise InvalidPasswordResetTokenError()

        user = await self._user_repo.get_by_id(reset_token.user_id)
        if user is None:
            # Conta desativada/soft-deleted entre o request e o confirm — mesmo
            # `code` genérico dos outros casos, não revela o motivo real.
            raise InvalidPasswordResetTokenError()

        await self._password_reset_repo.mark_used(reset_token.id)
        await self._user_repo.update_password(user.id, hash_password(new_password))
        # Uma senha comprometida o bastante para justificar reset também compromete
        # qualquer sessão já aberta com a senha antiga — mesmo efeito de `logout_all`.
        await self._revoke_all_sessions(user.id)

    async def _revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        sessions = await self._session_repo.list_active_by_user(user_id)
        for session in sessions:
            await self._session_repo.revoke_session(session.id)

    async def _issue_refresh_token(self, session_id: uuid.UUID) -> tuple[str, RefreshToken]:
        plain = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
        token = RefreshToken(
            session_id=session_id, token_hash=hash_refresh_token(plain), expires_at=expires_at
        )
        created = await self._session_repo.create_refresh_token(token)
        return plain, created
