import secrets
from collections.abc import AsyncGenerator, Iterator

import pytest
from redis.asyncio import from_url
from src.core.config import get_settings
from src.features.github.client import GitHubInstallationInfo
from src.features.github.dependencies import get_github_app_client
from src.main import app

from tests.unit.features.github.fakes import FakeGitHubAppClient


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


@pytest.fixture(autouse=True)
async def _clear_metrics() -> AsyncGenerator[None, None]:
    """`AccessLogMiddleware` grava em `metrics:*` a cada requisição (Sprint 14.5)
    — sem isolar aqui, um teste que afirma uma contagem exata de `GET /metrics`
    ficaria dependente da ordem/quantidade de requisições dos testes anteriores
    no mesmo arquivo ou em arquivos anteriores da suíte.
    """
    redis = from_url(get_settings().redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    async for key in redis.scan_iter("metrics:*"):
        await redis.delete(key)
    yield
    await redis.aclose()


@pytest.fixture
def installation_id() -> int:
    """Os testes de contrato gravam no banco de verdade, sem rollback entre execuções,
    e `installation_id` é único entre todos os workspaces — um id fixo faria a
    segunda execução da suíte esbarrar na conexão gravada pela primeira."""
    return secrets.randbelow(10**12) + 10**9


@pytest.fixture
def github_client(installation_id: int) -> Iterator[FakeGitHubAppClient]:
    fake = FakeGitHubAppClient(
        [
            GitHubInstallationInfo(
                installation_id=installation_id,
                account_login="acme-org",
                account_type="Organization",
                suspended_at=None,
            )
        ]
    )
    app.dependency_overrides[get_github_app_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_github_app_client, None)
