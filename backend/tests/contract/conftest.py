from collections.abc import AsyncGenerator

import pytest
from redis.asyncio import from_url
from src.core.config import get_settings


@pytest.fixture(autouse=True)
async def _clear_login_rate_limit() -> AsyncGenerator[None, None]:
    """Todo teste de contrato que passa por `/auth/register`/`/auth/login` compartilha
    a mesma janela de rate limit (Redis real, chaveado por IP — não uma transação
    revertida por teste), então sem isolar aqui um teste consumiria o limite do
    próximo em qualquer arquivo desta pasta.
    """
    redis = from_url(get_settings().redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    async for key in redis.scan_iter("ratelimit:*"):
        await redis.delete(key)
    yield
    await redis.aclose()
