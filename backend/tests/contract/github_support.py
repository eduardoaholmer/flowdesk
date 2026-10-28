"""Helpers compartilhados pelos testes de contrato da integração com o GitHub
(Sprint 10.1/10.2): conta, workspace e conexão de uma instalação pelo fluxo real.
As fixtures `installation_id`/`github_client` ficam em `conftest.py`."""

import uuid
from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def register_and_login(client: AsyncClient) -> str:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    token: str = response.json()["data"]["access_token"]
    return token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_workspace(client: AsyncClient, owner_token: str) -> str:
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=auth(owner_token)
    )
    workspace_id: str = created.json()["data"]["id"]
    return workspace_id


async def invite_and_accept(
    client: AsyncClient, workspace_id: str, owner_token: str, role: str
) -> str:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Grace Hopper", "email": email, "password": "Str0ng!Passw0rd"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    token: str = login.json()["data"]["access_token"]
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": email, "role": role},
        headers=auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=auth(token)
    )
    return token


async def connect(client: AsyncClient, workspace_id: str, token: str) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/connect", headers=auth(token)
    )
    assert response.status_code == 200
    state: str = parse_qs(urlparse(response.json()["data"]["install_url"]).query)["state"][0]
    return state


async def return_from_github(
    client: AsyncClient, state: str, installation_id: int | str
) -> tuple[int, str]:
    response = await client.get(
        "/api/v1/integrations/github/setup",
        params={
            "state": state,
            "code": "github-code",
            "installation_id": str(installation_id),
            "setup_action": "install",
        },
        follow_redirects=False,
    )
    return response.status_code, response.headers["location"]
