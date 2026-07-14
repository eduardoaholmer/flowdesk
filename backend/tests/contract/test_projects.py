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


async def _create_project(
    client: AsyncClient, workspace_id: str, token: str, name: str = "Roadmap", **extra: object
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": name, **extra},
        headers=_auth(token),
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def test_create_project_generates_slug_and_records_creator(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Public Roadmap", "color": "#4F46E5", "icon": "rocket"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["name"] == "Public Roadmap"
    assert body["slug"].startswith("public-roadmap")
    assert body["status"] == "ACTIVE"
    assert body["color"] == "#4F46E5"
    assert body["workspace_id"] == workspace_id


async def test_create_project_rejects_duplicate_name_case_insensitive(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    await _create_project(client, workspace_id, owner_token, name="Roadmap")

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "ROADMAP"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "project_name_taken"


async def test_create_project_rejects_taken_slug(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    await _create_project(client, workspace_id, owner_token, name="Roadmap", slug="roadmap")

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Other Project", "slug": "roadmap"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "project_slug_taken"


async def test_create_project_requires_authentication(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects", json={"name": "Roadmap"}
    )

    assert response.status_code == 401


async def test_list_projects_paginates_and_returns_only_workspace_scoped(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    for i in range(3):
        await _create_project(client, workspace_id, owner_token, name=f"Project {i}")
    _, other_owner_token = await _register_and_login(client)
    other_workspace_id = await _create_workspace(client, other_owner_token)
    await _create_project(
        client, other_workspace_id, other_owner_token, name="Other Workspace Project"
    )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects",
        params={"page": 1, "per_page": 2},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2
    assert len(body["data"]) == 2


async def test_list_projects_filters_by_search_and_status(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    onboarding = await _create_project(client, workspace_id, owner_token, name="Onboarding Flow")
    await _create_project(client, workspace_id, owner_token, name="Legacy Import")
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{onboarding['id']}/archive",
        headers=_auth(owner_token),
    )

    search_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects",
        params={"search": "onboarding"},
        headers=_auth(owner_token),
    )
    status_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects",
        params={"status": "ARCHIVED"},
        headers=_auth(owner_token),
    )

    assert search_response.json()["meta"]["total"] == 1
    assert search_response.json()["data"][0]["id"] == onboarding["id"]
    assert status_response.json()["meta"]["total"] == 1
    assert status_response.json()["data"][0]["status"] == "ARCHIVED"


async def test_get_project_hides_existence_from_non_member(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project = await _create_project(client, workspace_id, owner_token)
    _, outsider_token = await _register_and_login(client)

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}",
        headers=_auth(outsider_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "workspace_not_found"


async def test_update_project_by_owner_succeeds_and_records_change(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project = await _create_project(client, workspace_id, owner_token)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}",
        json={"description": "Now with a description"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["description"] == "Now with a description"


async def test_update_project_requires_admin_or_owner(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project = await _create_project(client, workspace_id, owner_token)
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}",
        json={"name": "Hijacked"},
        headers=_auth(member_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_archive_then_restore_project(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project = await _create_project(client, workspace_id, owner_token)

    archive_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}/archive",
        headers=_auth(owner_token),
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "ARCHIVED"

    double_archive_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}/archive",
        headers=_auth(owner_token),
    )
    assert double_archive_response.status_code == 409
    assert double_archive_response.json()["error"]["code"] == "project_already_archived"

    restore_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}/restore",
        headers=_auth(owner_token),
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["status"] == "ACTIVE"

    double_restore_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}/restore",
        headers=_auth(owner_token),
    )
    assert double_restore_response.status_code == 409
    assert double_restore_response.json()["error"]["code"] == "project_not_archived"


async def test_delete_project_requires_owner_or_admin_and_soft_deletes(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    project = await _create_project(client, workspace_id, owner_token)

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}", headers=_auth(owner_token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/projects/{project['id']}", headers=_auth(owner_token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "project_not_found"


async def test_multi_tenant_isolation_across_two_workspaces(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = await _create_workspace(client, token_a)
    project_a = await _create_project(client, workspace_a, token_a)
    _, token_b = await _register_and_login(client)
    workspace_b = await _create_workspace(client, token_b)

    cross_get = await client.get(
        f"/api/v1/workspaces/{workspace_a}/projects/{project_a['id']}", headers=_auth(token_b)
    )
    assert cross_get.status_code == 404

    cross_list = await client.get(
        f"/api/v1/workspaces/{workspace_a}/projects", headers=_auth(token_b)
    )
    assert cross_list.status_code == 404

    own_list = await client.get(
        f"/api/v1/workspaces/{workspace_b}/projects", headers=_auth(token_b)
    )
    assert own_list.status_code == 200
    assert own_list.json()["meta"]["total"] == 0
