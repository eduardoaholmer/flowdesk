import uuid
from collections.abc import Sequence

from httpx import AsyncClient

# Cobre o critério de aceite da Sprint 5 (RBAC) em nível de contrato HTTP —
# a única camada que de fato exercita a cadeia completa
# `Depends(require_permission(...))` -> `PermissionService` -> service layer.
# Cenários: OWNER acessa tudo; ADMIN respeita limites (não exclui workspace,
# não gerencia OWNER); MEMBER/GUEST respeitam limites (sem ação
# administrativa); usuário fora do workspace não tem acesso (404, nunca 403).


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


async def _invite_and_join(
    client: AsyncClient, owner_token: str, workspace_id: str, role: str, email: str | None = None
) -> tuple[str, str]:
    email = email or _unique_email()
    _, token = await _register_and_login(client, email)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": email, "role": role},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(token)
    )
    return email, token


async def _member_id(client: AsyncClient, workspace_id: str, token: str, email: str) -> str:
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(token), params={"per_page": 100}
    )
    members: Sequence[dict[str, object]] = response.json()["data"]
    for member in members:
        user = member["user"]
        assert isinstance(user, dict)
        if user["email"] == email:
            member_id = member["id"]
            assert isinstance(member_id, str)
            return member_id
    raise AssertionError(f"member with email {email} not found")


async def test_owner_has_full_access(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_email, _ = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    member_id = await _member_id(client, workspace_id, owner_token, member_email)

    assert (
        await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(owner_token))
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Renamed"},
            headers=_auth(owner_token),
        )
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/invitations",
            json={"email": _unique_email(), "role": "MEMBER"},
            headers=_auth(owner_token),
        )
    ).status_code == 201
    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
            json={"role": "ADMIN"},
            headers=_auth(owner_token),
        )
    ).status_code == 200
    assert (
        await client.delete(
            f"/api/v1/workspaces/{workspace_id}/members/{member_id}", headers=_auth(owner_token)
        )
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/workspaces/{workspace_id}", headers=_auth(owner_token))
    ).status_code == 204


async def test_admin_respects_limits(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    admin_email, admin_token = await _invite_and_join(client, owner_token, workspace_id, "ADMIN")
    member_email, _ = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    member_id = await _member_id(client, workspace_id, owner_token, member_email)
    owner_member_id = await _member_id(client, workspace_id, owner_token, owner_email)

    # ADMIN pode: ver, atualizar, convidar, gerenciar um MEMBER.
    assert (
        await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(admin_token))
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Renamed"},
            headers=_auth(admin_token),
        )
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/invitations",
            json={"email": _unique_email(), "role": "MEMBER"},
            headers=_auth(admin_token),
        )
    ).status_code == 201
    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
            json={"role": "ADMIN"},
            headers=_auth(admin_token),
        )
    ).status_code == 200

    # ADMIN não pode: excluir o workspace, nem gerenciar um OWNER.
    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}", headers=_auth(admin_token)
    )
    assert delete_response.status_code == 403
    assert delete_response.json()["error"]["code"] == "permission_denied"

    manage_owner_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member_id}",
        json={"role": "MEMBER"},
        headers=_auth(admin_token),
    )
    assert manage_owner_response.status_code == 403
    assert manage_owner_response.json()["error"]["code"] == "cannot_manage_owner"

    remove_owner_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member_id}", headers=_auth(admin_token)
    )
    assert remove_owner_response.status_code == 403
    assert remove_owner_response.json()["error"]["code"] == "cannot_manage_owner"


async def test_member_respects_limits(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_email, member_token = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    other_email, _ = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    other_member_id = await _member_id(client, workspace_id, owner_token, other_email)

    # MEMBER pode ver o workspace e a lista de membros (workspace.view).
    assert (
        await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(member_token))
    ).status_code == 200
    assert (
        await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(member_token))
    ).status_code == 200

    # MEMBER não pode atualizar/excluir o workspace, convidar, nem gerenciar membros.
    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", json={"name": "Hijacked"}, headers=_auth(member_token)
    )
    assert update_response.status_code == 403

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}", headers=_auth(member_token)
    )
    assert delete_response.status_code == 403

    invite_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(member_token),
    )
    assert invite_response.status_code == 403

    manage_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{other_member_id}",
        json={"role": "ADMIN"},
        headers=_auth(member_token),
    )
    assert manage_response.status_code == 403

    remove_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{other_member_id}", headers=_auth(member_token)
    )
    assert remove_response.status_code == 403


async def test_guest_respects_limits(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    guest_email, guest_token = await _invite_and_join(client, owner_token, workspace_id, "GUEST")

    # GUEST pode visualizar o workspace (workspace.view).
    assert (
        await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(guest_token))
    ).status_code == 200

    # GUEST não pode atualizar o workspace nem convidar membros.
    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", json={"name": "Hijacked"}, headers=_auth(guest_token)
    )
    assert update_response.status_code == 403

    invite_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(guest_token),
    )
    assert invite_response.status_code == 403


async def test_outsider_has_no_access(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_email, _ = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    member_id = await _member_id(client, workspace_id, owner_token, member_email)
    _, outsider_token = await _register_and_login(client)

    # Não-membro recebe 404 em toda rota de recurso de tenant — nunca 403
    # (docs/07-security.md §9.1, anti-enumeration).
    for status_code, response in [
        (
            404,
            await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(outsider_token)),
        ),
        (
            404,
            await client.patch(
                f"/api/v1/workspaces/{workspace_id}",
                json={"name": "Hijacked"},
                headers=_auth(outsider_token),
            ),
        ),
        (
            404,
            await client.get(
                f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(outsider_token)
            ),
        ),
        (
            404,
            await client.post(
                f"/api/v1/workspaces/{workspace_id}/invitations",
                json={"email": _unique_email(), "role": "MEMBER"},
                headers=_auth(outsider_token),
            ),
        ),
        (
            404,
            await client.patch(
                f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
                json={"role": "ADMIN"},
                headers=_auth(outsider_token),
            ),
        ),
        (
            404,
            await client.delete(
                f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
                headers=_auth(outsider_token),
            ),
        ),
    ]:
        assert response.status_code == status_code
        assert response.json()["error"]["code"] == "workspace_not_found"


async def test_owner_cannot_manage_own_membership_via_admin_endpoints(
    client: AsyncClient,
) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    owner_member_id = await _member_id(client, workspace_id, owner_token, owner_email)

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member_id}",
        json={"role": "ADMIN"},
        headers=_auth(owner_token),
    )
    assert update_response.status_code == 409
    assert update_response.json()["error"]["code"] == "cannot_manage_own_membership"

    remove_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member_id}", headers=_auth(owner_token)
    )
    assert remove_response.status_code == 409
    assert remove_response.json()["error"]["code"] == "cannot_manage_own_membership"


async def _create_project(client: AsyncClient, workspace_id: str, token: str) -> str:
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Roadmap"},
        headers=_auth(token),
    )
    project_id: str = created.json()["data"]["id"]
    return project_id


async def test_owner_has_full_project_access(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            json={"name": "Discarded Probe"},
            headers=_auth(owner_token),
        )
    ).status_code == 201
    project_id = await _create_project(client, workspace_id, owner_token)
    assert (
        await client.get(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(owner_token)
        )
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
            json={"description": "desc"},
            headers=_auth(owner_token),
        )
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/archive",
            headers=_auth(owner_token),
        )
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/restore",
            headers=_auth(owner_token),
        )
    ).status_code == 200
    assert (
        await client.delete(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(owner_token)
        )
    ).status_code == 204


async def test_admin_has_full_project_access(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, admin_token = await _invite_and_join(client, owner_token, workspace_id, "ADMIN")
    project_id = await _create_project(client, workspace_id, owner_token)

    assert (
        await client.patch(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
            json={"description": "desc"},
            headers=_auth(admin_token),
        )
    ).status_code == 200
    assert (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/archive",
            headers=_auth(admin_token),
        )
    ).status_code == 200
    assert (
        await client.delete(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(admin_token)
        )
    ).status_code == 204


async def test_member_can_only_read_projects(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    project_id = await _create_project(client, workspace_id, owner_token)

    assert (
        await client.get(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(member_token)
        )
    ).status_code == 200

    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Member Attempt"},
        headers=_auth(member_token),
    )
    assert create_response.status_code == 403

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        json={"name": "Hijacked"},
        headers=_auth(member_token),
    )
    assert update_response.status_code == 403

    archive_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}/archive",
        headers=_auth(member_token),
    )
    assert archive_response.status_code == 403

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(member_token)
    )
    assert delete_response.status_code == 403


async def test_guest_can_only_read_projects(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, guest_token = await _invite_and_join(client, owner_token, workspace_id, "GUEST")
    project_id = await _create_project(client, workspace_id, owner_token)

    assert (
        await client.get(
            f"/api/v1/workspaces/{workspace_id}/projects/{project_id}", headers=_auth(guest_token)
        )
    ).status_code == 200

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        json={"name": "Hijacked"},
        headers=_auth(guest_token),
    )
    assert update_response.status_code == 403


async def test_outsider_has_no_project_access(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project_id = await _create_project(client, workspace_id, owner_token)
    _, outsider_token = await _register_and_login(client)

    for status_code, response in [
        (
            404,
            await client.get(
                f"/api/v1/workspaces/{workspace_id}/projects", headers=_auth(outsider_token)
            ),
        ),
        (
            404,
            await client.get(
                f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
                headers=_auth(outsider_token),
            ),
        ),
        (
            404,
            await client.post(
                f"/api/v1/workspaces/{workspace_id}/projects",
                json={"name": "Outsider Attempt"},
                headers=_auth(outsider_token),
            ),
        ),
        (
            404,
            await client.delete(
                f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
                headers=_auth(outsider_token),
            ),
        ),
    ]:
        assert response.status_code == status_code
        assert response.json()["error"]["code"] == "workspace_not_found"


async def test_update_member_role_rejects_promoting_to_owner(client: AsyncClient) -> None:
    owner_email, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_email, _ = await _invite_and_join(client, owner_token, workspace_id, "MEMBER")
    member_id = await _member_id(client, workspace_id, owner_token, member_email)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
        json={"role": "OWNER"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 422
