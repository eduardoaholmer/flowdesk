import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from redis.asyncio import from_url
from src.core.config import get_settings


@pytest.fixture(autouse=True)
async def _clear_login_rate_limit() -> AsyncGenerator[None, None]:
    """`/auth/login` é limitado por IP em uma janela real de Redis (não a
    transação Postgres revertida por teste) — sem isso, execuções consecutivas
    desta suíte poluiriam a janela umas das outras.
    """
    redis = from_url(get_settings().redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    async for key in redis.scan_iter("ratelimit:ip:*"):
        await redis.delete(key)
    yield
    async for key in redis.scan_iter("ratelimit:ip:*"):
        await redis.delete(key)
    await redis.aclose()


async def test_login_rate_limit_returns_429_after_five_attempts_per_ip(
    client: AsyncClient,
) -> None:
    payload = {"email": "nobody@example.com", "password": "wrong-password"}

    for _ in range(5):
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    blocked = await client.post("/api/v1/auth/login", json=payload)

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert "Retry-After" in blocked.headers


async def test_password_reset_request_rate_limit_returns_429_after_five_attempts_per_ip(
    client: AsyncClient,
) -> None:
    payload = {"email": "nobody@example.com"}

    for _ in range(5):
        response = await client.post("/api/v1/auth/password-reset/request", json=payload)
        assert response.status_code == 202

    blocked = await client.post("/api/v1/auth/password-reset/request", json=payload)

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert "Retry-After" in blocked.headers


async def test_password_reset_confirm_rate_limit_returns_429_after_five_attempts_per_ip(
    client: AsyncClient,
) -> None:
    payload = {"token": "not-a-real-token", "new_password": "N3w!StrongPassw0rd"}

    for _ in range(5):
        response = await client.post("/api/v1/auth/password-reset/confirm", json=payload)
        assert response.status_code == 401

    blocked = await client.post("/api/v1/auth/password-reset/confirm", json=payload)

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


async def test_unauthenticated_requests_to_protected_routes_are_rate_limited_by_ip(
    client: AsyncClient,
) -> None:
    """Antes do hardening desta sprint, uma requisição sem Bearer (ou com um Bearer
    inválido) a uma rota protegida não era limitada de jeito nenhum — só a rejeição
    de `get_current_user` a barrava, sem custo de rate limit."""
    for _ in range(60):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    blocked = await client.get("/api/v1/users/me")

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


async def test_authenticated_requests_are_not_limited_by_the_unauthenticated_bucket(
    client: AsyncClient,
) -> None:
    email = f"user-{uuid.uuid4().hex[:10]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    access_token = login_response.json()["data"]["access_token"]

    for _ in range(60):
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
