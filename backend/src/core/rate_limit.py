from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis, from_url

from src.core.config import get_settings

_redis: Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


def _get_redis() -> Redis:
    """Cliente Redis com escopo por event loop, não um singleton fixo no import.

    Um cliente assíncrono prende sua conexão ao event loop em que foi criado —
    reusá-lo depois que esse loop fechou derruba a próxima chamada com
    `RuntimeError: Event loop is closed` (mesma classe de problema que
    `tests/conftest.py::db_engine` já documenta para o engine do Postgres, só
    que ali resolvido via fixture; aqui, como este módulo é código de produção
    sem controle de fixture de teste, o recreate-on-loop-change precisa viver
    no próprio módulo). Em produção há um único loop pela vida do processo,
    então isto se comporta como um singleton normal, sem custo extra.
    """
    global _redis, _redis_loop
    loop = asyncio.get_running_loop()
    if _redis is None or _redis_loop is not loop:
        # `from_url` não tem anotação de retorno em redis-py (biblioteca externa,
        # não código nosso) — chamada não tipada aceita mesmo sob `mypy --strict`.
        _redis = from_url(  # type: ignore[no-untyped-call]
            get_settings().redis_url, decode_responses=True
        )
        _redis_loop = loop
    return _redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


async def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
    """Janela deslizante via sorted set (docs/07-security.md §6): cada requisição
    vira um membro com score = timestamp; membros fora da janela são podados a
    cada chamada, e o tamanho do set após a poda é a contagem real na janela.
    """
    redis = _get_redis()
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
    await _get_redis().ping()
