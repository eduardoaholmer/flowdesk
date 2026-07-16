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


async def _create_issue(
    client: AsyncClient, workspace_id: str, token: str, *, assignee_id: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {"title": "Corrigir bug"}
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues", json=payload, headers=_auth(token)
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def _member_user_id(client: AsyncClient, member_token: str) -> str:
    response = await client.get("/api/v1/users/me", headers=_auth(member_token))
    user_id: str = response.json()["data"]["id"]
    return user_id


async def _invite_mentionable_member(
    client: AsyncClient, workspace_id: str, owner_token: str
) -> tuple[str, str]:
    """`GET /notifications` não é isolado por workspace (é a caixa de entrada
    inteira do usuário — ver `NotificationRepository.list_by_user`), então
    reusar um e-mail fixo como "grace@example.com" entre testes deste arquivo
    faria o mesmo usuário real acumular notificações de testes anteriores.
    Cada teste precisa de seu próprio local-part único para mencionar.
    """
    local_part = f"mention-{uuid.uuid4().hex[:8]}"
    member_token = (
        await _invite_and_accept_member(
            client, workspace_id, owner_token, email=f"{local_part}@example.com"
        )
    )[1]
    return member_token, local_part


async def test_list_notifications_is_empty_for_new_user(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)

    response = await client.get("/api/v1/notifications", headers=_auth(owner_token))

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["total"] == 0


async def test_list_notifications_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/notifications")

    assert response.status_code == 401


async def test_comment_mention_creates_notification_for_mentioned_member(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_token, local_part = await _invite_mentionable_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": f"Olá @{local_part}, pode revisar?"},
        headers=_auth(owner_token),
    )
    response = await client.get("/api/v1/notifications", headers=_auth(member_token))

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    notification = body["data"][0]
    assert notification["type"] == "MENTION"
    assert notification["payload"]["issue_identifier"] == issue["identifier"]
    assert notification["read_at"] is None


async def test_issue_status_change_notifies_assignee(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    member_id = await _member_user_id(client, member_token)
    issue = await _create_issue(client, workspace_id, owner_token, assignee_id=member_id)

    await client.patch(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}",
        json={"status": "IN_PROGRESS"},
        headers=_auth(owner_token),
    )
    response = await client.get("/api/v1/notifications", headers=_auth(member_token))

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["type"] == "STATUS_CHANGE"


async def test_notifications_are_not_visible_to_other_users(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, local_part = await _invite_mentionable_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": f"Olá @{local_part}"},
        headers=_auth(owner_token),
    )

    owner_notifications = await client.get("/api/v1/notifications", headers=_auth(owner_token))

    assert owner_notifications.json()["meta"]["total"] == 0


async def test_mark_notification_read(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_token, local_part = await _invite_mentionable_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": f"Olá @{local_part}"},
        headers=_auth(owner_token),
    )
    notification_id = (
        await client.get("/api/v1/notifications", headers=_auth(member_token))
    ).json()["data"][0]["id"]

    response = await client.patch(
        f"/api/v1/notifications/{notification_id}", headers=_auth(member_token)
    )

    assert response.status_code == 200
    assert response.json()["data"]["read_at"] is not None


async def test_mark_notification_read_for_another_users_notification_is_not_found(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_token, local_part = await _invite_mentionable_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
        json={"body": f"Olá @{local_part}"},
        headers=_auth(owner_token),
    )
    notification_id = (
        await client.get("/api/v1/notifications", headers=_auth(member_token))
    ).json()["data"][0]["id"]

    response = await client.patch(
        f"/api/v1/notifications/{notification_id}", headers=_auth(owner_token)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "notification_not_found"


async def test_mark_all_read_clears_unread_count(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    member_token, local_part = await _invite_mentionable_member(client, workspace_id, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    for _ in range(2):
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/comments",
            json={"body": f"Olá @{local_part}"},
            headers=_auth(owner_token),
        )

    mark_all_response = await client.post(
        "/api/v1/notifications/mark-all-read", headers=_auth(member_token)
    )
    unread_after = await client.get(
        "/api/v1/notifications", params={"read": False}, headers=_auth(member_token)
    )

    assert mark_all_response.status_code == 204
    assert unread_after.json()["meta"]["total"] == 0
