import pytest
from src.core.config import Settings
from src.features.auth.exceptions import InvalidCredentialsError, OAuthProviderNotConfiguredError
from src.features.auth.oauth_providers import OAuthProfile, OAuthProvider
from src.features.auth.schemas import RegisterRequest
from src.features.auth.service import AuthService

from tests.unit.features.auth.fakes import (
    FakeMailSender,
    FakeOAuthClient,
    FakeOAuthIdentityRepository,
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
def oauth_identity_repo() -> FakeOAuthIdentityRepository:
    return FakeOAuthIdentityRepository()


@pytest.fixture
def google_client() -> FakeOAuthClient:
    return FakeOAuthClient(OAuthProvider.GOOGLE)


@pytest.fixture
def service(
    user_repo: FakeUserRepository,
    session_repo: FakeSessionRepository,
    settings: Settings,
    oauth_identity_repo: FakeOAuthIdentityRepository,
    google_client: FakeOAuthClient,
) -> AuthService:
    return AuthService(
        user_repo,
        session_repo,
        settings,
        FakePasswordResetRepository(),
        FakeMailSender(),
        oauth_identity_repo,
        {OAuthProvider.GOOGLE: google_client},
    )


def _profile(
    *, provider_user_id: str = "google-sub-1", email: str = "ada@example.com"
) -> OAuthProfile:
    return OAuthProfile(
        provider=OAuthProvider.GOOGLE,
        provider_user_id=provider_user_id,
        email=email,
        name="Ada Lovelace",
        avatar_url="https://provider.example/avatar.png",
    )


async def test_login_with_oauth_creates_new_user(
    service: AuthService, google_client: FakeOAuthClient, user_repo: FakeUserRepository
) -> None:
    google_client.register_profile("valid-code", _profile())

    result = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "valid-code", user_agent="pytest", ip_address="127.0.0.1"
    )

    assert result.user.email == "ada@example.com"
    assert result.user.password_hash is None
    assert result.user.avatar_url == "https://provider.example/avatar.png"
    assert result.access_token
    assert result.refresh_token
    assert len(user_repo.users) == 1


async def test_login_with_oauth_reuses_user_on_second_login(
    service: AuthService, google_client: FakeOAuthClient, user_repo: FakeUserRepository
) -> None:
    google_client.register_profile("code-1", _profile())
    google_client.register_profile("code-2", _profile())

    first = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "code-1", user_agent=None, ip_address=None
    )
    second = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "code-2", user_agent=None, ip_address=None
    )

    assert first.user.id == second.user.id
    assert len(user_repo.users) == 1


async def test_login_with_oauth_links_existing_account_by_email(
    service: AuthService,
    google_client: FakeOAuthClient,
    user_repo: FakeUserRepository,
    oauth_identity_repo: FakeOAuthIdentityRepository,
) -> None:
    """Alguém que já tem conta tradicional (senha) usa Google pela primeira vez com o
    mesmo e-mail — deve logar na MESMA conta, nunca criar uma segunda."""
    existing_user = await service.register(
        RegisterRequest(name="Ada Antiga", email="ada@example.com", password="Str0ng!Passw0rd")
    )
    google_client.register_profile("valid-code", _profile())

    result = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "valid-code", user_agent=None, ip_address=None
    )

    assert result.user.id == existing_user.id
    assert len(user_repo.users) == 1
    assert len(oauth_identity_repo.identities) == 1


async def test_login_with_oauth_does_not_overwrite_existing_avatar(
    service: AuthService, google_client: FakeOAuthClient, user_repo: FakeUserRepository
) -> None:
    existing_user = await service.register(
        RegisterRequest(name="Ada", email="ada@example.com", password="Str0ng!Passw0rd")
    )
    user_repo.users[existing_user.id].avatar_url = "https://existing.example/avatar.png"
    google_client.register_profile("valid-code", _profile())

    result = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "valid-code", user_agent=None, ip_address=None
    )

    assert result.user.avatar_url == "https://existing.example/avatar.png"


async def test_login_with_oauth_fills_missing_avatar_on_existing_account(
    service: AuthService, google_client: FakeOAuthClient, user_repo: FakeUserRepository
) -> None:
    user = await service.register(
        RegisterRequest(name="Ada", email="ada@example.com", password="Str0ng!Passw0rd")
    )
    assert user.avatar_url is None
    google_client.register_profile("valid-code", _profile())

    result = await service.login_with_oauth(
        OAuthProvider.GOOGLE, "valid-code", user_agent=None, ip_address=None
    )

    assert result.user.avatar_url == "https://provider.example/avatar.png"


async def test_login_with_oauth_raises_for_unconfigured_provider(service: AuthService) -> None:
    with pytest.raises(OAuthProviderNotConfiguredError):
        await service.login_with_oauth(
            OAuthProvider.GITHUB, "any-code", user_agent=None, ip_address=None
        )


async def test_build_oauth_authorize_url_raises_for_unconfigured_provider(
    service: AuthService,
) -> None:
    with pytest.raises(OAuthProviderNotConfiguredError):
        service.build_oauth_authorize_url(OAuthProvider.GITHUB, "some-state")


async def test_build_oauth_authorize_url_delegates_to_client(
    service: AuthService, google_client: FakeOAuthClient
) -> None:
    url = service.build_oauth_authorize_url(OAuthProvider.GOOGLE, "state-123")

    assert "state=state-123" in url
    assert google_client.authorize_url_calls == ["state-123"]


async def test_password_login_rejected_for_oauth_only_account(
    service: AuthService, google_client: FakeOAuthClient
) -> None:
    """Conta criada só via Google (sem senha) não pode logar com senha nenhuma —
    nem uma senha "adivinhada" corretamente, porque não existe hash para comparar."""
    google_client.register_profile("valid-code", _profile())
    await service.login_with_oauth(
        OAuthProvider.GOOGLE, "valid-code", user_agent=None, ip_address=None
    )

    with pytest.raises(InvalidCredentialsError):
        await service.login(
            "ada@example.com", "whatever-password", user_agent=None, ip_address=None
        )
