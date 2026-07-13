from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_engine: AsyncEngine = create_async_engine(get_settings().database_url, pool_pre_ping=True)

_session_factory = async_sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Uma sessão por requisição, injetada via Depends. Fechada ao final do request.

    Repositories recebem esta sessão; quem controla commit/rollback é o service
    (Unit of Work), nunca o repository — ver CLAUDE.md §6.
    """
    async with _session_factory() as session:
        yield session
