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


async def _list_states(
    client: AsyncClient, workspace_id: str, token: str
) -> list[dict[str, object]]:
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/workflow-states", headers=_auth(token)
    )
    data: list[dict[str, object]] = response.json()["data"]
    return data


async def test_workspace_creation_seeds_six_default_states(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    states = await _list_states(client, workspace_id, owner_token)

    assert [s["name"] for s in states] == [
        "Backlog",
        "Todo",
        "In Progress",
        "In Review",
        "Done",
        "Canceled",
    ]
    assert sum(1 for s in states if s["is_default"]) == 1


async def test_member_can_read_but_not_manage_states(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    _, member_token = await _invite_and_accept_member(client, workspace_id, owner_token)

    read_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/workflow-states", headers=_auth(member_token)
    )
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/workflow-states",
        json={"name": "Blocked", "category": "STARTED"},
        headers=_auth(member_token),
    )

    assert read_response.status_code == 200
    assert create_response.status_code == 403


async def test_admin_can_create_update_and_reorder_states(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)

    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/workflow-states",
        json={"name": "Blocked", "category": "STARTED"},
        headers=_auth(owner_token),
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["position"] == 6

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{created['id']}",
        json={"name": "Blocked (external)"},
        headers=_auth(owner_token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Blocked (external)"

    states = await _list_states(client, workspace_id, owner_token)
    reversed_ids = [s["id"] for s in reversed(states)]
    reorder_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/reorder",
        json={"ordered_ids": reversed_ids},
        headers=_auth(owner_token),
    )
    assert reorder_response.status_code == 200
    reordered = reorder_response.json()["data"]
    assert [s["id"] for s in reordered] == reversed_ids
    assert [s["position"] for s in reordered] == list(range(len(reordered)))


async def test_delete_without_issues_succeeds(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    states = await _list_states(client, workspace_id, owner_token)
    canceled = next(s for s in states if s["name"] == "Canceled")

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{canceled['id']}",
        headers=_auth(owner_token),
    )

    assert response.status_code == 204
    remaining_names = [s["name"] for s in await _list_states(client, workspace_id, owner_token)]
    assert "Canceled" not in remaining_names


async def test_delete_with_issues_requires_reassignment(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    states = await _list_states(client, workspace_id, owner_token)
    todo = next(s for s in states if s["name"] == "Todo")
    backlog = next(s for s in states if s["name"] == "Backlog")
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Issue presa no Todo", "status_id": todo["id"]},
        headers=_auth(owner_token),
    )

    blocked_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{todo['id']}",
        headers=_auth(owner_token),
    )
    assert blocked_response.status_code == 409
    assert blocked_response.json()["error"]["code"] == "workflow_state_has_issues"
    assert blocked_response.json()["error"]["details"]["issue_count"] == 1

    reassigned_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{todo['id']}",
        params={"reassign_to_id": backlog["id"]},
        headers=_auth(owner_token),
    )
    assert reassigned_response.status_code == 204

    issues = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues", headers=_auth(owner_token)
    )
    assert issues.json()["data"][0]["status_id"] == backlog["id"]


async def test_cannot_delete_last_remaining_state(client: AsyncClient) -> None:
    _, owner_token = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_token)
    states = await _list_states(client, workspace_id, owner_token)

    for state in states[:-1]:
        await client.delete(
            f"/api/v1/workspaces/{workspace_id}/workflow-states/{state['id']}",
            headers=_auth(owner_token),
        )

    last = (await _list_states(client, workspace_id, owner_token))[0]
    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{last['id']}",
        headers=_auth(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cannot_delete_last_workflow_state"
