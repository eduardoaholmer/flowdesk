from __future__ import annotations

import asyncio

from redis.asyncio import Redis, from_url

from src.core.config import get_settings

_redis: Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


def get_redis() -> Redis:
    """Cliente Redis com escopo por event loop, não um singleton fixo no import.

    Um cliente assíncrono prende sua conexão ao event loop em que foi criado —
    reusá-lo depois que esse loop fechou derruba a próxima chamada com
    `RuntimeError: Event loop is closed` (mesma classe de problema que
    `tests/conftest.py::db_engine` já documenta para o engine do Postgres, só
    que ali resolvido via fixture; aqui, como este módulo é código de produção
    sem controle de fixture de teste, o recreate-on-loop-change precisa viver
    no próprio módulo). Em produção há um único loop pela vida do processo,
    então isto se comporta como um singleton normal, sem custo extra.

    Extraído de `core/rate_limit.py` na Sprint 14.5 quando `core/metrics.py`
    precisou do mesmo cliente — dois módulos reimplementando este singleton
    duplicaria a lógica de recreate-on-loop-change, não só uma chamada trivial.
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
