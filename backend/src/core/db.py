import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings
from src.core.exceptions import FlowDeskError

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_engine_loop: asyncio.AbstractEventLoop | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Engine com escopo por event loop, não um singleton fixo no import.

    Uma engine assíncrona prende sua conexão ao loop em que foi criada — em
    produção há um único loop pela vida do processo (singleton normal, sem
    custo extra), mas sob `pytest-asyncio` (loop novo por função de teste) uma
    engine fixa no import quebra a segunda função de teste que a usa com
    `RuntimeError: Event loop is closed` (mesmo racional do `db_engine` em
    `tests/conftest.py`, aqui replicado porque este módulo é código de
    produção, não uma fixture controlável por teste).
    """
    global _engine, _session_factory, _engine_loop
    loop = asyncio.get_running_loop()
    if _engine is None or _engine_loop is not loop:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
        _session_factory = async_sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)
        _engine_loop = loop
    assert _session_factory is not None
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Uma sessão por requisição, injetada via Depends. Fechada ao final do request.

    Repositories recebem esta sessão; quem controla commit/rollback é o service
    (Unit of Work), nunca o repository — ver CLAUDE.md §6. Como cada método de
    service hoje mapeia 1:1 para uma requisição, o boundary transacional da
    "unidade de trabalho" é a própria requisição.

    Uma `FlowDeskError` é um resultado de negócio válido, não uma falha da
    transação (CLAUDE.md §7) — e pode carregar efeito colateral intencional que
    precisa persistir mesmo quando a requisição termina em erro. Exemplo real
    (`AuthService.refresh`): detectar reuso de refresh token revoga a sessão
    inteira *e então* lança `InvalidRefreshTokenError` — se essa exceção
    disparasse rollback, a revogação de defesa seria desfeita silenciosamente,
    deixando o token já rotacionado ainda válido — o oposto do pretendido.
    Por isso só uma exceção verdadeiramente inesperada (não mapeada) reverte.
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except FlowDeskError:
            await session.commit()
            raise
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
