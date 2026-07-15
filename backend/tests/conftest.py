from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from src.core.config import get_settings
from src.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """`ASGITransport` não dispara o lifespan do app (diferente do `TestClient` síncrono
    do Starlette) — sem isto, `app.state.started_at` nunca é setado e `GET /version`
    quebra em qualquer teste de contrato. `app.router.lifespan_context` é o mesmo
    context manager passado a `FastAPI(lifespan=...)` em `src/main.py`.
    """
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Assume que `alembic upgrade head` já rodou contra `DATABASE_URL` — testes de
    integração validam o comportamento dos repositories, não a criação do schema
    (isso é responsabilidade do próprio Alembic, verificado separadamente em CI).

    Escopo por teste (não por sessão): pytest-asyncio cria um event loop novo por
    função de teste por padrão, e um engine assíncrono não pode ser reaproveitado
    entre loops diferentes — compartilhá-lo via fixture `session`-scoped derruba a
    conexão na troca de loop (erro só visível no teardown, difícil de diagnosticar).
    """
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Uma conexão + transação por teste, revertida ao final — isolamento entre
    testes sem precisar truncar tabelas manualmente. Repositories nunca dão commit
    (CLAUDE.md §6), então tudo fica dentro dessa transação até o rollback.
    """
    async with db_engine.connect() as connection:
        trans = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
