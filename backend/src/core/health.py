import asyncio
import os
import time
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Literal

from src.core.config import get_settings
from src.core.db import ping_database
from src.core.logging import get_logger
from src.core.rate_limit import ping_redis

logger = get_logger(__name__)

CheckStatus = Literal["ok", "error"]


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: CheckStatus
    latency_ms: float
    detail: str | None = None


@dataclass(frozen=True)
class HealthReport:
    status: Literal["ok", "degraded"]
    checks: list[HealthCheckResult]


async def _run_check(name: str, probe: Awaitable[None]) -> HealthCheckResult:
    start = time.perf_counter()
    try:
        await probe
    except Exception as exc:  # noqa: BLE001 — ponto de agregação de falha de dependência externa, não lógica de negócio
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("health_check_failed", check=name, error=str(exc), latency_ms=latency_ms)
        # `/health/ready` não é autenticado (orquestrador não consegue autenticar um probe) —
        # `str(exc)` fica só no log estruturado, nunca na resposta HTTP, para não vazar detalhe
        # de infraestrutura (host/porta/credencial de driver) a qualquer chamador na internet.
        detail = None if get_settings().is_production else str(exc)
        return HealthCheckResult(name=name, status="error", latency_ms=latency_ms, detail=detail)
    return HealthCheckResult(
        name=name, status="ok", latency_ms=round((time.perf_counter() - start) * 1000, 2)
    )


def _check_storage() -> None:
    """Verifica que o diretório de upload existe e é gravável — mesma pasta que
    `LocalStorageProvider.save` usa (`core/storage.py`), sem escrever nenhum arquivo real."""
    upload_dir = get_settings().upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    if not os.access(upload_dir, os.W_OK):
        raise PermissionError(f"Diretório de upload não é gravável: {upload_dir}")


async def run_health_checks() -> HealthReport:
    """Registro de checagens de prontidão (`GET /health/ready`). Adicionar uma nova
    dependência externa (ex.: um provider de storage remoto) é uma linha nova aqui,
    sem tocar nas demais — estrutura preparada para novos serviços."""
    checks = await asyncio.gather(
        _run_check("database", ping_database()),
        _run_check("redis", ping_redis()),
        _run_check("storage", asyncio.to_thread(_check_storage)),
    )
    overall: Literal["ok", "degraded"] = (
        "ok" if all(check.status == "ok" for check in checks) else "degraded"
    )
    return HealthReport(status=overall, checks=list(checks))
