import uuid
from datetime import UTC, datetime, timedelta

import pytest
from src.core.config import Settings
from src.core.security import hash_refresh_token, verify_password
from src.features.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
)
from src.features.auth.schemas import RegisterRequest
from src.features.auth.service import AuthService

from tests.unit.features.auth.fakes import (
    FakeMailSender,
    FakePasswordResetRepository,
    FakeSessionRepository,
    FakeUserRepository,
)


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def session_repo() -> FakeSessionRepository:
    return FakeSessionRepository()


@pytest.fixture
def password_reset_repo() -> FakePasswordResetRepository:
    return FakePasswordResetRepository()


@pytest.fixture
def mail_sender() -> FakeMailSender:
    return FakeMailSender()


@pytest.fixture
def service(
    user_repo: FakeUserRepository,
    session_repo: FakeSessionRepository,
    settings: Settings,
    password_reset_repo: FakePasswordResetRepository,
    mail_sender: FakeMailSender,
) -> AuthService:
    return AuthService(user_repo, session_repo, settings, password_reset_repo, mail_sender)


def _register_payload(email: str = "ada@example.com") -> RegisterRequest:
    return RegisterRequest(name="Ada Lovelace", email=email, password="Str0ng!Passw0rd")


async def test_register_creates_user_with_hashed_password(service: AuthService) -> None:
    user = await service.register(_register_payload())

    assert user.id is not None
    assert user.email == "ada@example.com"
    assert user.password_hash != "Str0ng!Passw0rd"
    assert verify_password("Str0ng!Passw0rd", user.password_hash)


async def test_register_rejects_duplicate_email(service: AuthService) -> None:
    await service.register(_register_payload())

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(_register_payload())


async def test_login_succeeds_with_correct_credentials(service: AuthService) -> None:
    await service.register(_register_payload())

    result = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent="pytest", ip_address="127.0.0.1"
    )

    assert result.user.email == "ada@example.com"
    assert result.access_token
    assert result.refresh_token


async def test_login_rejects_wrong_password(service: AuthService) -> None:
    await service.register(_register_payload())

    with pytest.raises(InvalidCredentialsError):
        await service.login("ada@example.com", "wrong-password", user_agent=None, ip_address=None)


async def test_login_rejects_nonexistent_email(service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        await service.login(
            "nobody@example.com", "whatever-password", user_agent=None, ip_address=None
        )


async def test_refresh_rotates_token(
    service: AuthService, session_repo: FakeSessionRepository
) -> None:
    await service.register(_register_payload())
    login_result = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )

    refresh_result = await service.refresh(login_result.refresh_token)

    assert refresh_result.refresh_token != login_result.refresh_token
    assert refresh_result.access_token

    old_token_hash = hash_refresh_token(login_result.refresh_token)
    old_token = await session_repo.get_refresh_token_by_hash(old_token_hash)
    assert old_token is not None
    assert old_token.revoked_at is not None

    new_token_hash = hash_refresh_token(refresh_result.refresh_token)
    new_token = await session_repo.get_refresh_token_by_hash(new_token_hash)
    assert new_token is not None
    assert new_token.revoked_at is None
    assert old_token.replaced_by_id == new_token.id


async def test_refresh_rejects_unknown_token(service: AuthService) -> None:
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh("not-a-real-refresh-token")


async def test_refresh_rejects_expired_token(
    service: AuthService, session_repo: FakeSessionRepository
) -> None:
    await service.register(_register_payload())
    login_result = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )
    token_hash = hash_refresh_token(login_result.refresh_token)
    token = await session_repo.get_refresh_token_by_hash(token_hash)
    assert token is not None
    token.expires_at = datetime.now(UTC) - timedelta(days=1)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_result.refresh_token)


async def test_refresh_reuse_revokes_whole_session(
    service: AuthService, session_repo: FakeSessionRepository
) -> None:
    """Reapresentar um refresh token já rotacionado deve revogar toda a sessão —
    inclusive o token novo emitido na rotação — não só recusar a requisição atual.
    """
    await service.register(_register_payload())
    login_result = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )

    refresh_result = await service.refresh(login_result.refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_result.refresh_token)

    new_token_hash = hash_refresh_token(refresh_result.refresh_token)
    new_token = await session_repo.get_refresh_token_by_hash(new_token_hash)
    assert new_token is not None
    assert new_token.revoked_at is not None

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(refresh_result.refresh_token)


async def test_logout_revokes_session(
    service: AuthService, session_repo: FakeSessionRepository
) -> None:
    await service.register(_register_payload())
    login_result = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )

    await service.logout(login_result.refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_result.refresh_token)


async def test_logout_is_idempotent_when_token_missing(service: AuthService) -> None:
    await service.logout(None)
    await service.logout("some-token-that-does-not-exist")


async def test_logout_all_revokes_every_active_session(
    service: AuthService, user_repo: FakeUserRepository
) -> None:
    await service.register(_register_payload())
    login_1 = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )
    login_2 = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )
    user_id: uuid.UUID = login_1.user.id

    await service.logout_all(user_id)

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_1.refresh_token)
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_2.refresh_token)


async def test_request_password_reset_creates_token_and_sends_mail(
    service: AuthService,
    password_reset_repo: FakePasswordResetRepository,
    mail_sender: FakeMailSender,
) -> None:
    await service.register(_register_payload())

    await service.request_password_reset("ada@example.com")

    assert len(password_reset_repo.tokens) == 1
    assert "ada@example.com" in mail_sender.sent_password_resets


async def test_request_password_reset_is_silent_for_unknown_email(
    service: AuthService,
    password_reset_repo: FakePasswordResetRepository,
    mail_sender: FakeMailSender,
) -> None:
    await service.request_password_reset("nobody@example.com")

    assert password_reset_repo.tokens == {}
    assert mail_sender.sent_password_resets == {}


async def test_request_password_reset_invalidates_previous_token(
    service: AuthService, password_reset_repo: FakePasswordResetRepository
) -> None:
    await service.register(_register_payload())
    await service.request_password_reset("ada@example.com")
    first_token = next(iter(password_reset_repo.tokens.values()))

    await service.request_password_reset("ada@example.com")

    assert first_token.used_at is not None
    assert len(password_reset_repo.tokens) == 2


async def test_confirm_password_reset_changes_password(
    service: AuthService, user_repo: FakeUserRepository, mail_sender: FakeMailSender
) -> None:
    await service.register(_register_payload())
    await service.request_password_reset("ada@example.com")
    plain_token = mail_sender.sent_password_resets["ada@example.com"]

    await service.confirm_password_reset(plain_token, "N3w!StrongPassw0rd")

    updated_user = await user_repo.get_by_email("ada@example.com")
    assert updated_user is not None
    assert verify_password("N3w!StrongPassw0rd", updated_user.password_hash)
    assert not verify_password("Str0ng!Passw0rd", updated_user.password_hash)


async def test_confirm_password_reset_rejects_unknown_token(service: AuthService) -> None:
    with pytest.raises(InvalidPasswordResetTokenError):
        await service.confirm_password_reset("not-a-real-token", "N3w!StrongPassw0rd")


async def test_confirm_password_reset_rejects_expired_token(
    service: AuthService,
    password_reset_repo: FakePasswordResetRepository,
    mail_sender: FakeMailSender,
) -> None:
    await service.register(_register_payload())
    await service.request_password_reset("ada@example.com")
    plain_token = mail_sender.sent_password_resets["ada@example.com"]
    token = next(iter(password_reset_repo.tokens.values()))
    token.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.confirm_password_reset(plain_token, "N3w!StrongPassw0rd")


async def test_confirm_password_reset_rejects_reused_token(
    service: AuthService, mail_sender: FakeMailSender
) -> None:
    await service.register(_register_payload())
    await service.request_password_reset("ada@example.com")
    plain_token = mail_sender.sent_password_resets["ada@example.com"]
    await service.confirm_password_reset(plain_token, "N3w!StrongPassw0rd")

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.confirm_password_reset(plain_token, "Another!Passw0rd2")


async def test_confirm_password_reset_revokes_all_active_sessions(
    service: AuthService, mail_sender: FakeMailSender
) -> None:
    await service.register(_register_payload())
    login_1 = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )
    login_2 = await service.login(
        "ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None
    )
    await service.request_password_reset("ada@example.com")
    plain_token = mail_sender.sent_password_resets["ada@example.com"]

    await service.confirm_password_reset(plain_token, "N3w!StrongPassw0rd")

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_1.refresh_token)
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(login_2.refresh_token)


async def test_confirm_password_reset_allows_login_with_new_password(
    service: AuthService, mail_sender: FakeMailSender
) -> None:
    await service.register(_register_payload())
    await service.request_password_reset("ada@example.com")
    plain_token = mail_sender.sent_password_resets["ada@example.com"]

    await service.confirm_password_reset(plain_token, "N3w!StrongPassw0rd")

    with pytest.raises(InvalidCredentialsError):
        await service.login("ada@example.com", "Str0ng!Passw0rd", user_agent=None, ip_address=None)
    result = await service.login(
        "ada@example.com", "N3w!StrongPassw0rd", user_agent=None, ip_address=None
    )
    assert result.access_token
