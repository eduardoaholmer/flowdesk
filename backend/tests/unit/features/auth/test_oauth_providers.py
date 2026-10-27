import httpx
import pytest
from src.features.auth import oauth_providers
from src.features.auth.exceptions import OAuthProviderError
from src.features.auth.oauth_providers import GoogleOAuthClient


def _install_google_transport(monkeypatch: pytest.MonkeyPatch, userinfo: dict[str, object]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "provider-token"})
        return httpx.Response(200, json=userinfo)

    real_client = httpx.AsyncClient

    def client_factory(**kwargs: object) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(oauth_providers.httpx, "AsyncClient", client_factory)


def _client() -> GoogleOAuthClient:
    return GoogleOAuthClient(
        client_id="id", client_secret="secret", redirect_uri="https://app.example/cb"
    )


async def test_google_profile_with_verified_email_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_google_transport(
        monkeypatch, {"sub": "123", "email": "ada@example.com", "email_verified": True}
    )

    profile = await _client().fetch_profile("code")

    assert profile.email == "ada@example.com"
    assert profile.provider_user_id == "123"


@pytest.mark.parametrize("email_verified", [False, None, "true"])
async def test_google_profile_without_verified_email_is_rejected(
    monkeypatch: pytest.MonkeyPatch, email_verified: object
) -> None:
    userinfo: dict[str, object] = {"sub": "123", "email": "ada@example.com"}
    if email_verified is not None:
        userinfo["email_verified"] = email_verified
    _install_google_transport(monkeypatch, userinfo)

    with pytest.raises(OAuthProviderError):
        await _client().fetch_profile("code")
