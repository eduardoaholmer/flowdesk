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
    OAuthProviderNotConfiguredError,
)
from src.features.auth.models import OAuthIdentity, PasswordResetToken, RefreshToken, Session, User
from src.features.auth.oauth_providers import OAuthClientProtocol, OAuthProfile, OAuthProvider
from src.features.auth.repository import (
    OAuthIdentityRepositoryProtocol,
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
        oauth_identity_repo: OAuthIdentityRepositoryProtocol,
        oauth_clients: dict[OAuthProvider, OAuthClientProtocol],
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._settings = settings
        self._password_reset_repo = password_reset_repo
        self._mail_sender = mail_sender
        self._oauth_identity_repo = oauth_identity_repo
        # Só contém entrada para provedor com `client_id` configurado
        # (`AuthDependencies.get_auth_service`) — um provedor ausente aqui é
        # exatamente "desligado neste ambiente" (`OAuthProviderNotConfiguredError`).
        self._oauth_clients = oauth_clients

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
        if user is None or user.password_hash is None:
            # `password_hash is None` é uma conta criada só via login social
            # (`register()`/`login_with_oauth` nunca preenchem senha para ela) —
            # mesmo `code` genérico de "e-mail inexistente" (anti-enumeration,
            # docs/07-security.md §10): não revelamos que o e-mail existe, só sem senha.
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

    def build_oauth_authorize_url(self, provider: OAuthProvider, state: str) -> str:
        client = self._oauth_clients.get(provider)
        if client is None:
            raise OAuthProviderNotConfiguredError()
        return client.authorize_url(state)

    async def login_with_oauth(
        self,
        provider: OAuthProvider,
        code: str,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> LoginResult:
        """Troca o `code` pelo profile do provedor e resolve o `User` correspondente
        (RF social-auth, `docs/09-decision-log.md` ADR-061):

        1. Identidade já vinculada (`oauth_identities`) -> é o mesmo usuário de sempre.
        2. Nenhuma identidade, mas já existe conta com este e-mail (tradicional ou de
           outro provedor) -> vincula a identidade a essa conta em vez de duplicar
           (RF "evitar contas duplicadas") — seguro porque o e-mail aqui já foi
           verificado pelo provedor, ao contrário de um e-mail informado livremente
           pelo usuário.
        3. Nenhuma das duas -> cria conta nova, sem senha (`password_hash=None`).
        """
        client = self._oauth_clients.get(provider)
        if client is None:
            raise OAuthProviderNotConfiguredError()

        profile = await client.fetch_profile(code)
        user = await self._resolve_oauth_user(profile)

        session = await self._session_repo.create_session(
            Session(user_id=user.id, user_agent=user_agent, ip_address=ip_address)
        )
        refresh_token_plain, _ = await self._issue_refresh_token(session.id)
        access_token = create_access_token(user.id, self._settings)

        return LoginResult(user=user, access_token=access_token, refresh_token=refresh_token_plain)

    async def _resolve_oauth_user(self, profile: OAuthProfile) -> User:
        identity = await self._oauth_identity_repo.get_by_provider_identity(
            profile.provider.value, profile.provider_user_id
        )
        if identity is not None:
            user = await self._user_repo.get_by_id(identity.user_id)
            if user is not None:
                return user
            # Conta desativada/soft-deleted entre o vínculo original e este login —
            # trata como identidade nova de novo (mesmo e-mail pode ter sido
            # liberado), não como erro.

        user = await self._user_repo.get_by_email(profile.email)
        if user is None:
            user = await self._user_repo.create(
                User(name=profile.name, email=profile.email, avatar_url=profile.avatar_url)
            )
        elif user.avatar_url is None and profile.avatar_url is not None:
            # "Não sobrescrever informações existentes sem necessidade" — só completa
            # o que faltava, nunca substitui um avatar que a pessoa já tinha.
            user.avatar_url = profile.avatar_url

        await self._oauth_identity_repo.create(
            OAuthIdentity(
                user_id=user.id,
                provider=profile.provider.value,
                provider_user_id=profile.provider_user_id,
            )
        )
        return user

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
