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


async def test_create_workspace_makes_creator_owner_and_generates_slug(
    client: AsyncClient,
) -> None:
    _, token = await _register_and_login(client)

    response = await client.post(
        "/api/v1/workspaces", json={"name": "Acme Inc"}, headers=_auth(token)
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["name"] == "Acme Inc"
    assert body["slug"]

    members = await client.get(f"/api/v1/workspaces/{body['id']}/members", headers=_auth(token))
    assert members.status_code == 200
    assert members.json()["data"][0]["role"] == "OWNER"


async def test_create_workspace_rejects_taken_slug(client: AsyncClient) -> None:
    _, token = await _register_and_login(client)
    await client.post(
        "/api/v1/workspaces", json={"name": "Acme", "slug": "acme-corp"}, headers=_auth(token)
    )

    response = await client.post(
        "/api/v1/workspaces", json={"name": "Acme 2", "slug": "acme-corp"}, headers=_auth(token)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "slug_taken"


async def test_create_workspace_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/workspaces", json={"name": "Acme"})

    assert response.status_code == 401


async def test_list_workspaces_returns_only_own_and_paginates(client: AsyncClient) -> None:
    _, token = await _register_and_login(client)
    await client.post("/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(token))
    _, other_token = await _register_and_login(client)
    await client.post("/api/v1/workspaces", json={"name": "Other Co"}, headers=_auth(other_token))

    response = await client.get("/api/v1/workspaces", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["name"] == "Acme"


async def test_get_workspace_hides_existence_from_non_member(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    _, outsider_token = await _register_and_login(client)

    response = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=_auth(outsider_token))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "workspace_not_found"


async def test_update_workspace_requires_owner(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
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
        f"/api/v1/workspaces/{workspace_id}", json={"name": "Hijacked"}, headers=_auth(member_token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_update_workspace_by_owner_succeeds_and_records_change(
    client: AsyncClient,
) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"name": "Acme Renamed", "description": "desc"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["name"] == "Acme Renamed"
    assert body["description"] == "desc"


async def test_delete_workspace_requires_owner_and_soft_deletes(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}", headers=_auth(owner_token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=_auth(owner_token)
    )
    assert get_response.status_code == 404


async def test_full_invitation_flow_create_list_accept(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    invitee_email, invitee_token = await _register_and_login(client)

    invite_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": invitee_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    assert invite_response.status_code == 201
    invite_body = invite_response.json()["data"]
    assert invite_body["token"]
    assert invite_body["status"] == "PENDING"

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/invitations", headers=_auth(owner_token)
    )
    assert list_response.status_code == 200
    assert list_response.json()["meta"]["total"] == 1

    accept_response = await client.post(
        f"/api/v1/invitations/{invite_body['token']}/accept", headers=_auth(invitee_token)
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["data"]["role"] == "MEMBER"

    members_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(owner_token)
    )
    emails = {m["user"]["email"] for m in members_response.json()["data"]}
    assert invitee_email in emails


async def test_invitation_create_requires_owner_or_admin(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(member_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_invitation_accept_rejects_wrong_email(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    _, someone_else_token = await _register_and_login(client)

    response = await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept",
        headers=_auth(someone_else_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "invitation_email_mismatch"


async def test_invitation_accept_rejects_invalid_token(client: AsyncClient) -> None:
    _, token = await _register_and_login(client)

    response = await client.post(
        "/api/v1/invitations/not-a-real-token/accept", headers=_auth(token)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invitation_not_found"


async def test_invitation_create_rejects_duplicate_pending(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    payload = {"email": _unique_email(), "role": "MEMBER"}
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations", json=payload, headers=_auth(owner_token)
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations", json=payload, headers=_auth(owner_token)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invitation_already_pending"


async def test_invitation_create_rejects_existing_member(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "ADMIN"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_member"


async def test_cancel_invitation(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    invitation_id = invite.json()["data"]["id"]

    cancel_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}", headers=_auth(owner_token)
    )
    assert cancel_response.status_code == 204

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/invitations", headers=_auth(owner_token)
    )
    assert list_response.json()["meta"]["total"] == 0


async def test_leave_workspace_as_sole_owner_is_rejected(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/me", headers=_auth(owner_token)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "sole_owner_cannot_leave"


async def test_leave_workspace_as_regular_member_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )

    leave_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/me", headers=_auth(member_token)
    )
    assert leave_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=_auth(member_token)
    )
    assert get_response.status_code == 404


async def test_multi_tenant_isolation_across_two_workspaces(client: AsyncClient) -> None:
    _, token_a = await _register_and_login(client)
    workspace_a = (
        await client.post(
            "/api/v1/workspaces", json={"name": "Workspace A"}, headers=_auth(token_a)
        )
    ).json()["data"]
    _, token_b = await _register_and_login(client)
    workspace_b = (
        await client.post(
            "/api/v1/workspaces", json={"name": "Workspace B"}, headers=_auth(token_b)
        )
    ).json()["data"]

    cross_get = await client.get(f"/api/v1/workspaces/{workspace_b['id']}", headers=_auth(token_a))
    assert cross_get.status_code == 404

    cross_update = await client.patch(
        f"/api/v1/workspaces/{workspace_b['id']}", json={"name": "Hijacked"}, headers=_auth(token_a)
    )
    assert cross_update.status_code == 404

    cross_delete = await client.delete(
        f"/api/v1/workspaces/{workspace_b['id']}", headers=_auth(token_a)
    )
    assert cross_delete.status_code == 404

    cross_invite = await client.post(
        f"/api/v1/workspaces/{workspace_b['id']}/invitations",
        json={"email": _unique_email(), "role": "MEMBER"},
        headers=_auth(token_a),
    )
    assert cross_invite.status_code == 404

    own_list = await client.get("/api/v1/workspaces", headers=_auth(token_a))
    assert [w["id"] for w in own_list.json()["data"]] == [workspace_a["id"]]


async def test_transfer_ownership_by_owner_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    member_email, member_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": member_email, "role": "MEMBER"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(member_token)
    )
    members = (
        await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(owner_token))
    ).json()["data"]
    target_member = next(m for m in members if m["user"]["email"] == member_email)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members/{target_member['id']}/transfer-ownership",
        headers=_auth(owner_token),
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["owner_id"] == target_member["user"]["id"]

    updated_members = (
        await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(owner_token))
    ).json()["data"]
    roles_by_email = {m["user"]["email"]: m["role"] for m in updated_members}
    assert roles_by_email[member_email] == "OWNER"


async def test_transfer_ownership_requires_owner(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    admin_email, admin_token = await _register_and_login(client)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invitations",
        json={"email": admin_email, "role": "ADMIN"},
        headers=_auth(owner_token),
    )
    await client.post(
        f"/api/v1/invitations/{invite.json()['data']['token']}/accept", headers=_auth(admin_token)
    )
    members = (
        await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(owner_token))
    ).json()["data"]
    owner_member = next(m for m in members if m["role"] == "OWNER")

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member['id']}/transfer-ownership",
        headers=_auth(admin_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_transfer_ownership_rejects_unknown_member(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members/{uuid.uuid4()}/transfer-ownership",
        headers=_auth(owner_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "member_not_found"


async def test_transfer_ownership_rejects_self_target(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(owner_token)
    )
    workspace_id = created.json()["data"]["id"]
    members = (
        await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=_auth(owner_token))
    ).json()["data"]
    owner_member = members[0]

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members/{owner_member['id']}/transfer-ownership",
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cannot_transfer_ownership_to_self"


async def test_users_me_includes_workspace_memberships(client: AsyncClient) -> None:
    _, token = await _register_and_login(client)
    created = await client.post("/api/v1/workspaces", json={"name": "Acme"}, headers=_auth(token))
    workspace_id = created.json()["data"]["id"]

    response = await client.get("/api/v1/users/me", headers=_auth(token))

    assert response.status_code == 200
    workspaces = response.json()["data"]["workspaces"]
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == workspace_id
    assert workspaces[0]["role"] == "OWNER"
