from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_ready_reports_all_dependencies_ok(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    for check_name in ("database", "redis", "storage"):
        assert body["checks"][check_name]["status"] == "ok"


async def test_version_returns_api_version_and_environment(client: AsyncClient) -> None:
    response = await client.get("/version")

    assert response.status_code == 200
    body = response.json()
    assert "version" in body
    assert "environment" in body
    assert body["uptime_seconds"] >= 0


async def test_responses_include_security_headers(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in response.headers


async def test_malformed_json_body_returns_standard_error_envelope(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        content="{not valid json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list)


async def test_unknown_route_returns_standard_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"


async def test_metrics_counts_requests_grouped_by_route_template(client: AsyncClient) -> None:
    for _ in range(3):
        await client.get("/health")

    response = await client.get("/metrics")

    assert response.status_code == 200
    endpoints = {
        f"{entry['method']} {entry['route']}": entry for entry in response.json()["endpoints"]
    }
    entry = endpoints["GET /health"]
    assert entry["request_count"] >= 3
    assert entry["latency_p95_ms"] is not None
    assert entry["latency_p95_ms"] >= 0


async def test_metrics_groups_unmatched_routes_under_a_single_label(client: AsyncClient) -> None:
    await client.get("/api/v1/does-not-exist-a")
    await client.get("/api/v1/does-not-exist-b")

    response = await client.get("/metrics")

    endpoints = response.json()["endpoints"]
    unmatched = [entry for entry in endpoints if entry["route"] == "<unmatched>"]
    assert len(unmatched) == 1
    assert unmatched[0]["request_count"] == 2
