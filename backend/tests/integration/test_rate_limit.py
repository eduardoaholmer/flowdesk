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
