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


async def _create_issue(client: AsyncClient, workspace_id: str, token: str) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir bug"},
        headers=_auth(token),
    )
    data: dict[str, object] = response.json()["data"]
    return data


async def _upload(
    client: AsyncClient,
    workspace_id: str,
    issue_id: str,
    token: str,
    *,
    file_name: str = "print.png",
    content: bytes = b"fake-png-bytes",
    content_type: str = "image/png",
):
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue_id}/attachments",
        files={"file": (file_name, content, content_type)},
        headers=_auth(token),
    )


async def test_upload_attachment_succeeds_and_records_activity(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await _upload(client, workspace_id, issue["id"], owner_token)

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["file_name"] == "print.png"
    assert body["content_type"] == "image/png"
    assert body["storage_provider"] == "local"
    assert body["issue_id"] == issue["id"]

    activity = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/activity",
        headers=_auth(owner_token),
    )
    assert "attachment.uploaded" in [entry["action"] for entry in activity.json()["data"]]


async def test_list_issue_attachments_is_scoped_to_issue(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    other_issue = await _create_issue(client, workspace_id, owner_token)
    await _upload(client, workspace_id, issue["id"], owner_token, file_name="a.png")
    await _upload(client, workspace_id, other_issue["id"], owner_token, file_name="b.png")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/attachments",
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    names = [item["file_name"] for item in response.json()["data"]]
    assert names == ["a.png"]


async def test_upload_attachment_rejects_disallowed_content_type(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)

    response = await _upload(
        client,
        workspace_id,
        issue["id"],
        owner_token,
        file_name="virus.exe",
        content_type="application/x-msdownload",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "attachment_type_not_allowed"


async def test_upload_attachment_for_missing_issue_returns_404(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    response = await _upload(client, workspace_id, str(uuid.uuid4()), owner_token)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "issue_not_found"


async def test_guest_can_upload_attachment(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, guest_token = await _invite_and_accept_member(
        client, workspace_id, owner_token, role="GUEST"
    )

    response = await _upload(client, workspace_id, issue["id"], guest_token)

    assert response.status_code == 201


async def test_download_attachment_returns_file_bytes(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    uploaded = (
        await _upload(client, workspace_id, issue["id"], owner_token, content=b"hello-world")
    ).json()["data"]

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    assert response.content == b"hello-world"


async def test_download_attachment_requires_workspace_membership(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    uploaded = (await _upload(client, workspace_id, issue["id"], owner_token)).json()["data"]
    _, outsider_token = await _register_and_login(client)

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(outsider_token),
    )

    assert response.status_code == 404


async def test_delete_attachment_by_uploader_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    uploaded = (await _upload(client, workspace_id, issue["id"], member_token)).json()["data"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(member_token),
    )
    download_after_delete = await client.get(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(owner_token),
    )

    assert response.status_code == 204
    assert download_after_delete.status_code == 404


async def test_delete_attachment_by_non_uploader_member_is_forbidden(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    uploaded = (await _upload(client, workspace_id, issue["id"], owner_token)).json()["data"]
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(member_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_delete_attachment_by_admin_succeeds_without_being_uploader(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    issue = await _create_issue(client, workspace_id, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)
    uploaded = (await _upload(client, workspace_id, issue["id"], member_token)).json()["data"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/attachments/{uploaded['id']}",
        headers=_auth(owner_token),
    )

    assert response.status_code == 204


async def test_multi_tenant_isolation_for_attachments(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = await _create_workspace(client, token_a)
    issue_a = await _create_issue(client, workspace_a, token_a)
    uploaded = (await _upload(client, workspace_a, issue_a["id"], token_a)).json()["data"]
    _, token_b = await _register_and_login(client)

    cross_delete = await client.delete(
        f"/api/v1/workspaces/{workspace_a}/attachments/{uploaded['id']}", headers=_auth(token_b)
    )

    assert cross_delete.status_code == 404
