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


async def _create_label(
    client: AsyncClient, workspace_id: str, token: str, name: str = "bug", color: str = "#FF0000"
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/labels",
        json={"name": name, "color": color},
        headers=_auth(token),
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def test_create_label_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/labels",
        json={"name": "bug", "color": "#FF0000", "description": "Algo quebrado"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["name"] == "bug"
    assert body["color"] == "#FF0000"
    assert body["description"] == "Algo quebrado"
    assert body["issue_count"] == 0


async def test_label_issue_count_reflects_applied_issues(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)

    created_issue = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir login"},
        headers=_auth(owner_token),
    )
    issue_id = created_issue.json()["data"]["id"]
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue_id}/labels",
        json={"label_id": label["id"]},
        headers=_auth(owner_token),
    )

    listed = await client.get(
        f"/api/v1/workspaces/{workspace_id}/labels", headers=_auth(owner_token)
    )
    counts = {item["id"]: item["issue_count"] for item in listed.json()["data"]}
    assert counts[label["id"]] == 1


async def test_create_label_rejects_invalid_color(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/labels",
        json={"name": "bug", "color": "not-a-color"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 422


async def test_create_label_rejects_duplicate_name_in_workspace(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    await _create_label(client, workspace_id, owner_token, name="bug")

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/labels",
        json={"name": "bug", "color": "#00FF00"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "label_name_taken"


async def test_guest_cannot_create_label(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, guest_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, role="GUEST"
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/labels",
        json={"name": "bug", "color": "#FF0000"},
        headers=_auth(guest_token),
    )

    assert response.status_code == 403


async def test_list_labels_is_scoped_to_workspace(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    await _create_label(client, workspace_id, owner_token, name="bug")
    _, other_owner_token = await _register_and_login(client)
    other_workspace_id = await _create_workspace(client, other_owner_token)
    await _create_label(client, other_workspace_id, other_owner_token, name="feature")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/labels", headers=_auth(owner_token)
    )

    assert response.status_code == 200
    names = [label["name"] for label in response.json()["data"]]
    assert names == ["bug"]


async def test_update_label_renames_and_recolors(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/labels/{label['id']}",
        json={"name": "defeito", "color": "#0000FF"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "defeito"
    assert response.json()["data"]["color"] == "#0000FF"


async def test_member_cannot_update_or_delete_label(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/labels/{label['id']}",
        json={"name": "hijacked"},
        headers=_auth(member_token),
    )
    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/labels/{label['id']}", headers=_auth(member_token)
    )

    assert update_response.status_code == 403
    assert delete_response.status_code == 403


async def test_delete_label_soft_deletes_it(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/labels/{label['id']}", headers=_auth(owner_token)
    )
    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/labels/{label['id']}", headers=_auth(owner_token)
    )

    assert response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "label_not_found"


async def test_multi_tenant_isolation_for_labels(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = await _create_workspace(client, token_a)
    label_a = await _create_label(client, workspace_a, token_a)
    _, token_b = await _register_and_login(client)

    cross_get = await client.get(
        f"/api/v1/workspaces/{workspace_a}/labels/{label_a['id']}", headers=_auth(token_b)
    )
    cross_list = await client.get(
        f"/api/v1/workspaces/{workspace_a}/labels", headers=_auth(token_b)
    )

    assert cross_get.status_code == 404
    assert cross_list.status_code == 404


async def test_add_and_remove_label_on_issue(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)
    issue = (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/issues",
            json={"title": "Corrigir bug"},
            headers=_auth(owner_token),
        )
    ).json()["data"]

    add_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        json={"label_id": label["id"]},
        headers=_auth(owner_token),
    )
    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        headers=_auth(owner_token),
    )
    remove_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels/{label['id']}",
        headers=_auth(owner_token),
    )
    list_after_remove = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        headers=_auth(owner_token),
    )

    assert add_response.status_code == 201
    assert [item["id"] for item in list_response.json()["data"]] == [label["id"]]
    assert remove_response.status_code == 204
    assert list_after_remove.json()["data"] == []


async def test_add_label_to_issue_twice_is_conflict(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    label = await _create_label(client, workspace_id, owner_token)
    issue = (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/issues",
            json={"title": "Corrigir bug"},
            headers=_auth(owner_token),
        )
    ).json()["data"]
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        json={"label_id": label["id"]},
        headers=_auth(owner_token),
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        json={"label_id": label["id"]},
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "issue_label_already_applied"


async def test_add_label_from_other_workspace_to_issue_is_not_found(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = (
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/issues",
            json={"title": "Corrigir bug"},
            headers=_auth(owner_token),
        )
    ).json()["data"]
    _, other_owner_token = await _register_and_login(client)
    other_workspace_id = await _create_workspace(client, other_owner_token)
    foreign_label = await _create_label(client, other_workspace_id, other_owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/labels",
        json={"label_id": foreign_label["id"]},
        headers=_auth(owner_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "label_not_found"
