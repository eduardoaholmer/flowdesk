import base64
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
import pytest
from src.features.github import client as github_client_module
from src.features.github.client import GitHubAppClient
from src.features.github.exceptions import GitHubAuthorizationFailedError

Handler = Callable[[httpx.Request], httpx.Response]


def _install_transport(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    real_client = httpx.AsyncClient

    def client_factory(**kwargs: object) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(recording_handler))

    monkeypatch.setattr(github_client_module.httpx, "AsyncClient", client_factory)
    return requests


def _installation(installation_id: int, login: str = "acme-org") -> dict[str, object]:
    return {
        "id": installation_id,
        "account": {"login": login, "type": "Organization"},
        "suspended_at": None,
    }


def _github_handler(
    pages: list[list[dict[str, object]]],
    *,
    token_response: httpx.Response | None = None,
    revoke_status: int = 204,
) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login/oauth/access_token":
            return token_response or httpx.Response(200, json={"access_token": "user-token"})
        if request.url.path == "/user/installations":
            page = int(request.url.params["page"])
            installations = pages[page - 1] if page <= len(pages) else []
            return httpx.Response(
                200, json={"total_count": sum(map(len, pages)), "installations": installations}
            )
        if request.method == "DELETE":
            return httpx.Response(revoke_status)
        return httpx.Response(404)

    return handler


def _client() -> GitHubAppClient:
    return GitHubAppClient(slug="flowdesk-test", client_id="Iv1.abc", client_secret="secret")


def test_installation_url_points_to_the_app_with_encoded_state() -> None:
    url = _client().installation_url("a b/c")

    assert url == "https://github.com/apps/flowdesk-test/installations/new?state=a+b%2Fc"


async def test_finds_installation_visible_to_the_user(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = _installation(42)
    entry["suspended_at"] = "2026-10-01T12:00:00Z"
    requests = _install_transport(monkeypatch, _github_handler([[_installation(7), entry]]))

    info = await _client().find_user_installation("code", 42)

    assert info is not None
    assert info.installation_id == 42
    assert info.account_login == "acme-org"
    assert info.account_type == "Organization"
    assert info.suspended_at == datetime(2026, 10, 1, 12, tzinfo=UTC)
    installations_request = next(r for r in requests if r.url.path == "/user/installations")
    assert installations_request.headers["Authorization"] == "Bearer user-token"


async def test_follows_pagination_until_the_installation_is_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_page = [_installation(i) for i in range(1, 101)]
    _install_transport(monkeypatch, _github_handler([first_page, [_installation(500)]]))

    info = await _client().find_user_installation("code", 500)

    assert info is not None
    assert info.installation_id == 500


async def test_returns_none_when_user_cannot_see_the_installation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_transport(monkeypatch, _github_handler([[_installation(7)]]))

    assert await _client().find_user_installation("code", 42) is None


async def test_invalid_code_is_an_authorization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """O GitHub responde 200 com `error` no corpo para um `code` inválido/expirado."""
    _install_transport(
        monkeypatch,
        _github_handler(
            [], token_response=httpx.Response(200, json={"error": "bad_verification_code"})
        ),
    )

    with pytest.raises(GitHubAuthorizationFailedError):
        await _client().find_user_installation("code", 42)


async def test_github_api_error_is_an_authorization_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login/oauth/access_token":
            return httpx.Response(200, json={"access_token": "user-token"})
        if request.url.path == "/user/installations":
            return httpx.Response(401, json={"message": "Bad credentials"})
        return httpx.Response(204)

    _install_transport(monkeypatch, handler)

    with pytest.raises(GitHubAuthorizationFailedError):
        await _client().find_user_installation("code", 42)


async def test_user_token_is_revoked_after_the_check(monkeypatch: pytest.MonkeyPatch) -> None:
    requests = _install_transport(monkeypatch, _github_handler([[_installation(42)]]))

    await _client().find_user_installation("code", 42)

    revoke = next(r for r in requests if r.method == "DELETE")
    assert revoke.url.path == "/applications/Iv1.abc/token"
    expected_auth = base64.b64encode(b"Iv1.abc:secret").decode()
    assert revoke.headers["Authorization"] == f"Basic {expected_auth}"
    assert b"user-token" in revoke.content


async def test_revocation_failure_does_not_undo_a_valid_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_transport(monkeypatch, _github_handler([[_installation(42)]], revoke_status=500))

    info = await _client().find_user_installation("code", 42)

    assert info is not None
