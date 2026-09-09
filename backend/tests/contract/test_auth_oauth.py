from httpx import AsyncClient


async def test_oauth_login_rejects_unknown_provider(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/facebook/login", follow_redirects=False)

    assert response.status_code == 422


async def test_oauth_login_redirects_to_frontend_when_provider_not_configured(
    client: AsyncClient,
) -> None:
    """Nenhum `GOOGLE_CLIENT_ID`/`GITHUB_CLIENT_ID` está configurado no ambiente de
    teste — clicar no botão deveria voltar para a SPA com um erro legível, nunca um
    JSON cru numa navegação de página inteira."""
    response = await client.get("/api/v1/auth/google/login", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers["location"]
    assert "/oauth/callback" in location
    assert "error=oauth_provider_not_configured" in location


async def test_oauth_callback_redirects_with_error_when_state_cookie_missing(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "some-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "/oauth/callback" in location
    assert "error=oauth_authentication_failed" in location


async def test_oauth_callback_redirects_with_error_when_state_mismatches_cookie(
    client: AsyncClient,
) -> None:
    client.cookies.set("oauth_state", "cookie-state-value")

    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "different-state-value"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "error=oauth_authentication_failed" in response.headers["location"]


async def test_oauth_callback_redirects_with_error_when_provider_reports_error(
    client: AsyncClient,
) -> None:
    client.cookies.set("oauth_state", "cookie-state-value")

    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"error": "access_denied", "state": "cookie-state-value"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "error=oauth_authentication_failed" in response.headers["location"]


async def test_oauth_callback_rejects_unknown_provider(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/facebook/callback", follow_redirects=False)

    assert response.status_code == 422
