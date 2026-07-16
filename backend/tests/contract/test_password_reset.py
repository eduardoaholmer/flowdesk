import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient, Response
from src.core.mail import get_mail_sender
from src.main import app


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def _register(client: AsyncClient, email: str) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )


def _extract_cookie(response: Response, name: str) -> str | None:
    for set_cookie in response.headers.get_list("set-cookie"):
        cookie_pair = set_cookie.split(";")[0]
        key, _, value = cookie_pair.partition("=")
        if key == name:
            return value
    return None


class _CapturingMailSender:
    """Substitui `LoggingMailSender` só nestes testes via `app.dependency_overrides`
    — o único jeito legítimo de obter o token em texto puro sem violar o próprio
    propósito de não devolvê-lo pela API (`core/mail.py`).
    """

    def __init__(self) -> None:
        self.sent: dict[str, str] = {}

    async def send_password_reset(self, *, email: str, token: str) -> None:
        self.sent[email] = token


@pytest.fixture
async def mail_sender() -> AsyncGenerator[_CapturingMailSender, None]:
    sender = _CapturingMailSender()
    app.dependency_overrides[get_mail_sender] = lambda: sender
    yield sender
    app.dependency_overrides.pop(get_mail_sender, None)


async def test_request_password_reset_returns_202_for_existing_email(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    email = _unique_email()
    await _register(client, email)

    response = await client.post("/api/v1/auth/password-reset/request", json={"email": email})

    assert response.status_code == 202
    assert email in mail_sender.sent


async def test_request_password_reset_returns_202_for_unknown_email(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    """Mesmo status/corpo para e-mail existente ou não — anti-enumeration
    (`docs/07-security.md` §10), mesmo racional de `invalid_credentials` no login."""
    response = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": _unique_email()}
    )

    assert response.status_code == 202
    assert response.json() is None
    assert mail_sender.sent == {}


async def test_request_password_reset_never_leaks_token_in_response(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    email = _unique_email()
    await _register(client, email)

    response = await client.post("/api/v1/auth/password-reset/request", json={"email": email})

    assert "token" not in response.text.lower()


async def test_confirm_password_reset_changes_password_and_allows_login(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    email = _unique_email()
    await _register(client, email)
    await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    token = mail_sender.sent[email]

    confirm_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "N3w!StrongPassw0rd"},
    )
    old_password_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    new_password_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "N3w!StrongPassw0rd"}
    )

    assert confirm_response.status_code == 204
    assert old_password_login.status_code == 401
    assert new_password_login.status_code == 200


async def test_confirm_password_reset_rejects_unknown_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "N3w!StrongPassw0rd"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_password_reset_token"


async def test_confirm_password_reset_rejects_reused_token(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    email = _unique_email()
    await _register(client, email)
    await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    token = mail_sender.sent[email]
    await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "N3w!StrongPassw0rd"},
    )

    response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "Another!Passw0rd2"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_password_reset_token"


async def test_confirm_password_reset_rejects_weak_new_password(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    email = _unique_email()
    await _register(client, email)
    await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    token = mail_sender.sent[email]

    response = await client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "weak"}
    )

    assert response.status_code == 422


async def test_confirm_password_reset_revokes_existing_sessions(
    client: AsyncClient, mail_sender: _CapturingMailSender
) -> None:
    """Sessões revogadas não derrubam um access token já emitido e ainda válido —
    não há blocklist de `jti` (ADR-005/008, melhoria futura não bloqueante) — mas
    o refresh token correspondente para de funcionar, mesmo comportamento de
    `logout_all` (ver `test_logout_all_revokes_every_session` em `test_auth.py`).
    """
    email = _unique_email()
    await _register(client, email)
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    refresh_cookie = _extract_cookie(login_response, "refresh_token")
    csrf_cookie = _extract_cookie(login_response, "csrf_token")
    assert csrf_cookie is not None
    await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    token = mail_sender.sent[email]

    await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "N3w!StrongPassw0rd"},
    )
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={refresh_cookie}; csrf_token={csrf_cookie}",
            "X-CSRF-Token": csrf_cookie,
        },
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["error"]["code"] == "invalid_refresh_token"
