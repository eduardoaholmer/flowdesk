import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient, Response
from redis.asyncio import from_url
from src.core.config import get_settings


@pytest.fixture(autouse=True)
async def _clear_login_rate_limit() -> AsyncGenerator[None, None]:
    """Vários testes deste arquivo chamam `/auth/login`/`/auth/register` — sem
    isolar a janela de rate limit (Redis real, não uma transação revertida),
    um teste consumiria o limite do próximo.
    """
    redis = from_url(get_settings().redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    async for key in redis.scan_iter("ratelimit:*"):
        await redis.delete(key)
    yield
    await redis.aclose()


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def _extract_cookie(response: Response, name: str) -> str | None:
    for set_cookie in response.headers.get_list("set-cookie"):
        cookie_pair = set_cookie.split(";")[0]
        key, _, value = cookie_pair.partition("=")
        if key == name:
            return value
    return None


async def _register_and_login(
    client: AsyncClient, email: str | None = None
) -> tuple[str, Response]:
    email = email or _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    return email, response


async def test_register_returns_201_with_user(client: AsyncClient) -> None:
    email = _unique_email()

    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["email"] == email
    assert "password_hash" not in body
    assert "password" not in body


async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": _unique_email(), "password": "weak"},
    )

    assert response.status_code == 422


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada 2", "email": email, "password": "Str0ng!Passw0rd"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


async def test_login_returns_access_token_and_sets_cookies(client: AsyncClient) -> None:
    email, response = await _register_and_login(client)

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["access_token"]
    assert body["user"]["email"] == email

    refresh_cookie = _extract_cookie(response, "refresh_token")
    csrf_cookie = _extract_cookie(response, "csrf_token")
    assert refresh_cookie is not None
    assert csrf_cookie is not None
    set_cookie_headers = "\n".join(response.headers.get_list("set-cookie")).lower()
    assert "httponly" in set_cookie_headers
    assert "secure" in set_cookie_headers
    assert "samesite=strict" in set_cookie_headers


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_login_rejects_nonexistent_user_with_same_error_as_wrong_password(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": _unique_email(), "password": "whatever-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_refresh_requires_csrf_header(client: AsyncClient) -> None:
    _, login_response = await _register_and_login(client)
    refresh_cookie = _extract_cookie(login_response, "refresh_token")

    response = await client.post(
        "/api/v1/auth/refresh", headers={"Cookie": f"refresh_token={refresh_cookie}"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_refresh_token"


async def test_refresh_rejects_mismatched_csrf_header(client: AsyncClient) -> None:
    _, login_response = await _register_and_login(client)
    refresh_cookie = _extract_cookie(login_response, "refresh_token")
    csrf_cookie = _extract_cookie(login_response, "csrf_token")
    assert csrf_cookie is not None

    response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={refresh_cookie}; csrf_token={csrf_cookie}",
            "X-CSRF-Token": "not-the-right-value",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_refresh_token"


async def test_refresh_rotates_token_and_old_token_stops_working(client: AsyncClient) -> None:
    _, login_response = await _register_and_login(client)
    refresh_cookie = _extract_cookie(login_response, "refresh_token")
    csrf_cookie = _extract_cookie(login_response, "csrf_token")
    assert csrf_cookie is not None
    cookie_header = f"refresh_token={refresh_cookie}; csrf_token={csrf_cookie}"

    refresh_response = await client.post(
        "/api/v1/auth/refresh", headers={"Cookie": cookie_header, "X-CSRF-Token": csrf_cookie}
    )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["access_token"]
    new_refresh_cookie = _extract_cookie(refresh_response, "refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_cookie

    replay_response = await client.post(
        "/api/v1/auth/refresh", headers={"Cookie": cookie_header, "X-CSRF-Token": csrf_cookie}
    )

    assert replay_response.status_code == 401
    assert replay_response.json()["error"]["code"] == "invalid_refresh_token"


async def test_logout_revokes_session(client: AsyncClient) -> None:
    _, login_response = await _register_and_login(client)
    access_token = login_response.json()["data"]["access_token"]
    refresh_cookie = _extract_cookie(login_response, "refresh_token")
    csrf_cookie = _extract_cookie(login_response, "csrf_token")

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Cookie": f"refresh_token={refresh_cookie}",
        },
    )
    assert logout_response.status_code == 204

    refresh_after_logout = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={refresh_cookie}; csrf_token={csrf_cookie}",
            "X-CSRF-Token": csrf_cookie or "",
        },
    )
    assert refresh_after_logout.status_code == 401


async def test_logout_requires_bearer_token(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


async def test_logout_all_revokes_every_session(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Grace Hopper", "email": email, "password": "Str0ng!Passw0rd"},
    )
    login_1 = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    login_2 = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )

    access_2 = login_2.json()["data"]["access_token"]
    refresh_1 = _extract_cookie(login_1, "refresh_token")
    csrf_1 = _extract_cookie(login_1, "csrf_token")

    logout_all_response = await client.post(
        "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {access_2}"}
    )
    assert logout_all_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "Cookie": f"refresh_token={refresh_1}; csrf_token={csrf_1}",
            "X-CSRF-Token": csrf_1 or "",
        },
    )
    assert refresh_response.status_code == 401
