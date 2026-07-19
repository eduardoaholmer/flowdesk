from __future__ import annotations

from dataclasses import dataclass

from src.core.redis_client import get_redis

_ROUTES_KEY = "metrics:routes"
_UNMATCHED_ROUTE_LABEL = "<unmatched>"
_MAX_LATENCY_SAMPLES = 1000


def _endpoint_id(method: str, route_template: str | None) -> str:
    return f"{method} {route_template or _UNMATCHED_ROUTE_LABEL}"


async def record_request(
    *, method: str, route_template: str | None, status_code: int, duration_ms: float
) -> None:
    """Registra uma requisição para agregação em `GET /metrics` (Sprint 14.5,
    docs/09-decision-log.md ADR-031) — contagem por endpoint e amostras de
    latência para o cálculo de p95.

    Chamado por `AccessLogMiddleware` (`core/middleware.py`) com o mesmo
    `duration_ms`/`status_code` já computados ali, sem medir a requisição de
    novo. Requisições sem rota casada (404 genuíno) são agrupadas sob um único
    rótulo (`_UNMATCHED_ROUTE_LABEL`) — sem isso, sondagem/scan externo criaria
    uma entrada nova por path tentado, crescendo o conjunto de rotas sem limite.
    """
    redis = get_redis()
    endpoint = _endpoint_id(method, route_template)

    async with redis.pipeline(transaction=True) as pipe:
        pipe.sadd(_ROUTES_KEY, endpoint)
        pipe.incr(f"metrics:requests:{endpoint}")
        if status_code >= 500:
            pipe.incr(f"metrics:errors5xx:{endpoint}")
        pipe.rpush(f"metrics:latencies:{endpoint}", duration_ms)
        # Mantém só as últimas `_MAX_LATENCY_SAMPLES` amostras (janela móvel
        # aproximada) — sem isso, a lista de latências cresceria sem limite pela
        # vida do processo, para sempre.
        pipe.ltrim(f"metrics:latencies:{endpoint}", -_MAX_LATENCY_SAMPLES, -1)
        await pipe.execute()


@dataclass(frozen=True)
class EndpointMetrics:
    method: str
    route: str
    request_count: int
    error_5xx_count: int
    latency_p95_ms: float | None


def _percentile(sorted_values: list[float], p: float) -> float:
    """Interpolação linear (mesmo método default do numpy) sobre uma lista já ordenada."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * p
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower_weight = upper_index - rank
    upper_weight = rank - lower_index
    return sorted_values[lower_index] * lower_weight + sorted_values[upper_index] * upper_weight


async def get_metrics_snapshot() -> list[EndpointMetrics]:
    """Lê o snapshot atual de métricas por endpoint, ordenado por rota para uma
    resposta determinística. `p95` é calculado em leitura (não a cada requisição)
    sobre no máximo `_MAX_LATENCY_SAMPLES` amostras — custo desprezível para o
    número de endpoints deste projeto.
    """
    redis = get_redis()
    endpoints = await redis.smembers(_ROUTES_KEY)

    results: list[EndpointMetrics] = []
    for endpoint in sorted(endpoints):
        method, route = endpoint.split(" ", 1)
        async with redis.pipeline(transaction=True) as pipe:
            pipe.get(f"metrics:requests:{endpoint}")
            pipe.get(f"metrics:errors5xx:{endpoint}")
            pipe.lrange(f"metrics:latencies:{endpoint}", 0, -1)
            request_count_raw, error_count_raw, latencies_raw = await pipe.execute()

        latencies = sorted(float(value) for value in latencies_raw)
        results.append(
            EndpointMetrics(
                method=method,
                route=route,
                request_count=int(request_count_raw or 0),
                error_5xx_count=int(error_count_raw or 0),
                latency_p95_ms=round(_percentile(latencies, 0.95), 2) if latencies else None,
            )
        )
    return results
