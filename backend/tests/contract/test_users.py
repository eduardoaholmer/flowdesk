import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def test_get_me_returns_current_user_profile(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["email"] == email
    assert "password_hash" not in body


async def test_get_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


async def test_get_me_rejects_garbage_bearer_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
