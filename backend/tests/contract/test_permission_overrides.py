import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def _register_and_login(client: AsyncClient, email: str | None = None) -> tuple[str, str]:
    email = email or _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "Str0ng!Passw0rd"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ng!Passw0rd"}
    )
    return email, response.json()["data"]["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_workspace(client: AsyncClient, owner_token: str) -> str:
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id: str = created.json()["data"]["id"]
    return workspace_id


async def _invite_and_accept_member(
    client: AsyncClient, workspace_id: str, owner_token: str, role: str = "MEMBER"
) -> tuple[str, str]:
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": role},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )
    return member_email, member_token


def _matrix_entry(
    entries: list[dict[str, object]], role: str, permission: str
) -> dict[str, object]:
    return next(e for e in entries if e["role"] == role and e["permission"] == permission)


async def test_owner_sees_full_matrix_for_the_three_overridable_roles(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides", headers=_auth(owner_token)
    )

    assert response.status_code == 200
    entries = response.json()["data"]
    roles = {e["role"] for e in entries}
    assert roles == {"ADMIN", "MEMBER", "GUEST"}
    assert all(e["is_override"] is False for e in entries)
    assert all(e["effective"] == e["default"] for e in entries)


async def test_member_cannot_view_or_manage_permission_matrix(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    read_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides", headers=_auth(member_token)
    )
    write_response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "MEMBER", "permission": "issue.create", "granted": False},
        headers=_auth(member_token),
    )

    assert read_response.status_code == 403
    assert write_response.status_code == 403


async def test_admin_cannot_manage_permission_matrix_either(client: AsyncClient) -> None:
    """Gerenciar overrides é exclusivo do OWNER (`workspace.manage_permissions`,
    Sprint 9.3/ADR-058) — mesmo ADMIN, que já gerencia membros/status, não
    gerencia a própria régua de permissões (evita auto-escalonamento)."""
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, admin_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, role="ADMIN"
    )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides", headers=_auth(admin_token)
    )

    assert response.status_code == 403


async def test_granting_a_permission_actually_changes_member_behavior(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, guest_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, role="GUEST"
    )

    before = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Issue de um convidado"},
        headers=_auth(guest_token),
    )
    assert before.status_code == 403

    grant_response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "GUEST", "permission": "issue.create", "granted": True},
        headers=_auth(owner_token),
    )
    assert grant_response.status_code == 200
    entry = _matrix_entry(grant_response.json()["data"], "GUEST", "issue.create")
    assert entry["effective"] is True
    assert entry["is_override"] is True

    after = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Issue de um convidado"},
        headers=_auth(guest_token),
    )
    assert after.status_code == 201


async def test_revoking_a_permission_actually_blocks_member_behavior(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    before = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Issue de um membro"},
        headers=_auth(member_token),
    )
    assert before.status_code == 201

    revoke_response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "MEMBER", "permission": "issue.create", "granted": False},
        headers=_auth(owner_token),
    )
    assert revoke_response.status_code == 200
    entry = _matrix_entry(revoke_response.json()["data"], "MEMBER", "issue.create")
    assert entry["effective"] is False
    assert entry["is_override"] is True

    after = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Outra issue de um membro"},
        headers=_auth(member_token),
    )
    assert after.status_code == 403


async def test_setting_back_to_default_clears_the_override(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "MEMBER", "permission": "issue.create", "granted": False},
        headers=_auth(owner_token),
    )
    reset_response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "MEMBER", "permission": "issue.create", "granted": True},
        headers=_auth(owner_token),
    )

    entry = _matrix_entry(reset_response.json()["data"], "MEMBER", "issue.create")
    assert entry["effective"] is True
    assert entry["is_override"] is False


async def test_cannot_override_owner_role(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "OWNER", "permission": "issue.create", "granted": False},
        headers=_auth(owner_token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "cannot_override_owner_role"


async def test_cannot_override_a_locked_permission(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "ADMIN", "permission": "workspace.delete", "granted": True},
        headers=_auth(owner_token),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "locked_permission"
