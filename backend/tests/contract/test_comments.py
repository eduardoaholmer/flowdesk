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
    client: AsyncClient,
    workspace_id: str,
    owner_token: str,
    role: str = "MEMBER",
    email: str | None = None,
) -> tuple[str, str]:
    member_email, member_token = await _register_and_login(client, email)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": role},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )
    return member_email, member_token


async def _create_issue(client: AsyncClient, workspace_id: str, token: str) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir bug"},
        headers=_auth(token),
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def test_create_comment_succeeds_and_appears_in_issue_activity(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "Primeiro comentário"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["body"] == "Primeiro comentário"
    assert body["issue_id"] == issue["id"]
    assert body["mentioned_user_ids"] == []

    activity = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/activity",
        headers=_auth(owner_token),
    )
    assert "comment.created" in [entry["action"] for entry in activity.json()["data"]]


async def test_create_comment_rejects_empty_body(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "   "},
        headers=_auth(owner_token),
    )

    assert response.status_code == 422


async def test_create_comment_for_missing_issue_returns_404(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{uuid.uuid4()}/comments",
        json={"body": "oi"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "issue_not_found"


async def test_create_comment_detects_mention_by_email_local_part(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_email, member_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, email="grace@example.com"
    )
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "Olá @grace, pode revisar?"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 201
    mentioned = response.json()["data"]["mentioned_user_ids"]
    assert len(mentioned) == 1


async def test_guest_can_comment_but_not_create_issue(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, guest_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, role="GUEST"
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "Comentário de convidado"},
        headers=_auth(guest_token),
    )

    assert response.status_code == 201


async def test_list_comments_paginates_ordered_by_creation(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    for i in range(3):
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
            json={"body": f"comentário {i}"},
            headers=_auth(owner_token),
        )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        params={"page": 1, "per_page": 2},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 3
    assert len(body["data"]) == 2
    assert body["data"][0]["body"] == "comentário 0"


async def test_update_comment_by_author_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "original"},
        headers=_auth(member_token),
    )
    comment_id = created.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/comments/{comment_id}",
        json={"body": "editado"},
        headers=_auth(member_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["body"] == "editado"


async def test_update_comment_by_non_author_member_is_forbidden(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "original"},
        headers=_auth(owner_token),
    )
    comment_id = created.json()["data"]["id"]
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/comments/{comment_id}",
        json={"body": "hijacked"},
        headers=_auth(member_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_delete_comment_by_author_succeeds_and_hides_from_list(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "original"},
        headers=_auth(owner_token),
    )
    comment_id = created.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/comments/{comment_id}", headers=_auth(owner_token)
    )
    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        headers=_auth(owner_token),
    )

    assert response.status_code == 204
    assert list_response.json()["meta"]["total"] == 0


async def test_delete_comment_by_admin_succeeds_without_being_author(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": "original"},
        headers=_auth(member_token),
    )
    comment_id = created.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/comments/{comment_id}", headers=_auth(owner_token)
    )

    assert response.status_code == 204


async def test_multi_tenant_isolation_for_comments(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = await _create_workspace(client, token_a)
    issue_a = await _create_issue(client, workspace_a, token_a)
    await client.post(
        f"/api/v1/workspaces/{workspace_a}/issues/{issue_a['id']}/comments",
        json={"body": "secreto"},
        headers=_auth(token_a),
    )
    _, token_b = await _register_and_login(client)

    cross_list = await client.get(
        f"/api/v1/workspaces/{workspace_a}/issues/{issue_a['id']}/comments", headers=_auth(token_b)
    )

    assert cross_list.status_code == 404
