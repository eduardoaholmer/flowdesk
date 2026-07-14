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


async def _create_issue(
    client: AsyncClient, workspace_id: str, token: str, title: str = "Corrigir bug", **extra: object
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": title, **extra},
        headers=_auth(token),
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def test_create_issue_generates_identifier_and_records_creator(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir bug de login", "priority": "HIGH"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["title"] == "Corrigir bug de login"
    assert body["identifier"] == "FD-1"
    assert body["number"] == 1
    assert body["status"] == "BACKLOG"
    assert body["priority"] == "HIGH"
    assert body["version"] == 1
    assert body["workspace_id"] == workspace_id


async def test_create_issue_numbers_are_sequential_per_workspace(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    first = await _create_issue(client, workspace_id, owner_token, title="Primeira")
    second = await _create_issue(client, workspace_id, owner_token, title="Segunda")

    assert first["identifier"] == "FD-1"
    assert second["identifier"] == "FD-2"


async def test_create_issue_requires_authentication(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues", json={"title": "Issue"}
    )

    assert response.status_code == 401


async def test_create_issue_rejects_project_from_another_workspace(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, other_owner_token = await _register_and_login(client)
    other_workspace_id = await _create_workspace(client, other_owner_token)
    other_project = await client.post(
        f"/api/v1/workspaces/{other_workspace_id}/projects",
        json={"name": "Roadmap"},
        headers=_auth(other_owner_token),
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Issue", "project_id": other_project.json()["data"]["id"]},
        headers=_auth(owner_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


async def test_list_issues_paginates_and_returns_only_workspace_scoped(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    for i in range(3):
        await _create_issue(client, workspace_id, owner_token, title=f"Issue {i}")
    _, other_owner_token = await _register_and_login(client)
    other_workspace_id = await _create_workspace(client, other_owner_token)
    await _create_issue(
        client, other_workspace_id, other_owner_token, title="Other Workspace Issue"
    )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues",
        params={"page": 1, "per_page": 2},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2
    assert len(body["data"]) == 2


async def test_list_issues_filters_by_status_priority_and_creator(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    todo = await _create_issue(client, workspace_id, owner_token, title="A fazer", status="TODO")
    await _create_issue(client, workspace_id, owner_token, title="Urgente", priority="URGENT")

    status_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues",
        params={"status": "TODO"},
        headers=_auth(owner_token),
    )
    priority_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues",
        params={"priority": "URGENT"},
        headers=_auth(owner_token),
    )

    assert status_response.json()["meta"]["total"] == 1
    assert status_response.json()["data"][0]["id"] == todo["id"]
    assert priority_response.json()["meta"]["total"] == 1
    assert priority_response.json()["data"][0]["priority"] == "URGENT"


async def test_list_issues_search_matches_title_description_and_identifier(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    target = await _create_issue(
        client,
        workspace_id,
        owner_token,
        title="Corrigir vazamento de memória",
        description="detalhe",
    )
    await _create_issue(client, workspace_id, owner_token, title="Outra issue não relacionada")

    by_title = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues",
        params={"q": "vazamento"},
        headers=_auth(owner_token),
    )
    by_identifier = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues",
        params={"q": str(target["identifier"])},
        headers=_auth(owner_token),
    )

    assert by_title.json()["meta"]["total"] == 1
    assert by_title.json()["data"][0]["id"] == target["id"]
    assert by_identifier.json()["meta"]["total"] == 1
    assert by_identifier.json()["data"][0]["id"] == target["id"]


async def test_get_issue_hides_existence_from_non_member(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, outsider_token = await _register_and_login(client)

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=_auth(outsider_token)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "workspace_not_found"


async def test_update_issue_changes_status_and_records_activity(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}",
        json={"status": "IN_PROGRESS"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "IN_PROGRESS"
    assert response.json()["data"]["version"] == 2

    activity = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/activity",
        headers=_auth(owner_token),
    )
    actions = [entry["action"] for entry in activity.json()["data"]]
    assert "issue.status_changed" in actions
    assert "issue.created" in actions


async def test_update_issue_rejects_stale_if_match(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    await client.patch(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}",
        json={"title": "Renomeada"},
        headers=_auth(owner_token),
    )

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}",
        json={"title": "Outra mudança"},
        headers={**_auth(owner_token), "If-Match": "1"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "version_conflict"


async def test_update_issue_requires_workspace_membership(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, outsider_token = await _register_and_login(client)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}",
        json={"title": "Hijacked"},
        headers=_auth(outsider_token),
    )

    assert response.status_code == 404


async def test_delete_issue_by_creator_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, member_token)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=_auth(member_token)
    )

    assert response.status_code == 204
    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=_auth(owner_token)
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "issue_not_found"


async def test_delete_issue_by_non_creator_member_is_forbidden(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=_auth(member_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_delete_issue_by_admin_succeeds_without_being_creator(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, member_token)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=_auth(owner_token)
    )

    assert response.status_code == 204


async def test_multi_tenant_isolation_across_two_workspaces(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = await _create_workspace(client, token_a)
    issue_a = await _create_issue(client, workspace_a, token_a)
    _, token_b = await _register_and_login(client)
    workspace_b = await _create_workspace(client, token_b)

    cross_get = await client.get(
        f"/api/v1/workspaces/{workspace_a}/issues/{issue_a['id']}", headers=_auth(token_b)
    )
    assert cross_get.status_code == 404

    cross_list = await client.get(
        f"/api/v1/workspaces/{workspace_a}/issues", headers=_auth(token_b)
    )
    assert cross_list.status_code == 404

    own_list = await client.get(f"/api/v1/workspaces/{workspace_b}/issues", headers=_auth(token_b))
    assert own_list.status_code == 200
    assert own_list.json()["meta"]["total"] == 0
