from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from src.core.redis_client import get_redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


async def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
    """Janela deslizante via sorted set (docs/07-security.md §6): cada requisição
    vira um membro com score = timestamp; membros fora da janela são podados a
    cada chamada, e o tamanho do set após a poda é a contagem real na janela.
    """
    redis = get_redis()
    now = time.time()
    redis_key = f"ratelimit:{key}"
    member = uuid.uuid4().hex

    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
        pipe.zadd(redis_key, {member: now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds)
        results = await pipe.execute()

    count = results[2]
    if count > limit:
        return RateLimitResult(allowed=False, retry_after_seconds=window_seconds)
    return RateLimitResult(allowed=True, retry_after_seconds=0)


async def ping_redis() -> None:
    """Round-trip mínimo contra o Redis, usado por `core/health.py`."""
    await get_redis().ping()
