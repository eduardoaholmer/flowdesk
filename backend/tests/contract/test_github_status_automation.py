import uuid
from collections.abc import Iterator

import pytest
from httpx import AsyncClient, Response
from src.core.config import Settings, get_settings
from src.main import app

from tests.contract.github_support import (
    auth,
    connect,
    create_workspace,
    invite_and_accept,
    register_and_login,
    return_from_github,
)
from tests.github_payloads import pull_request_payload, sign
from tests.unit.features.github.fakes import FakeGitHubAppClient

_SECRET = "contract-webhook-secret"


@pytest.fixture
def webhook_settings() -> Iterator[Settings]:
    settings = get_settings().model_copy(update={"github_webhook_secret": _SECRET})
    app.dependency_overrides[get_settings] = lambda: settings
    yield settings
    app.dependency_overrides.pop(get_settings, None)


async def _connected_workspace(client: AsyncClient, installation_id: int) -> tuple[str, str]:
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)
    await return_from_github(client, await connect(client, workspace_id, token), installation_id)
    return workspace_id, token


async def _state_ids_by_name(client: AsyncClient, workspace_id: str, token: str) -> dict:
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/workflow-states", headers=auth(token)
    )
    return {state["name"]: state["id"] for state in response.json()["data"]}


async def _automations(client: AsyncClient, workspace_id: str, token: str) -> Response:
    return await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/automations", headers=auth(token)
    )


async def _set_automation(
    client: AsyncClient, workspace_id: str, token: str, event: str, target: str | None
) -> Response:
    return await client.put(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/automations",
        json={"event": event, "target_state_id": target},
        headers=auth(token),
    )


async def _deliver_pull_request(client: AsyncClient, body: bytes) -> Response:
    return await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": str(uuid.uuid4()),
            "X-Hub-Signature-256": sign(_SECRET, body),
        },
    )


async def test_connecting_writes_the_default_rules(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    states = await _state_ids_by_name(client, workspace_id, token)

    response = await _automations(client, workspace_id, token)

    assert response.status_code == 200
    assert response.json()["data"] == [
        {"event": "PR_DRAFT", "target_state_id": states["In Progress"]},
        {"event": "PR_OPEN", "target_state_id": states["In Review"]},
        {"event": "PR_MERGED", "target_state_id": states["Done"]},
        {"event": "PR_CLOSED", "target_state_id": None},
    ]


async def test_merged_pull_request_moves_the_issue_to_done_via_github(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    states = await _state_ids_by_name(client, workspace_id, token)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir login"},
        headers=auth(token),
    )
    issue = created.json()["data"]

    delivered = await _deliver_pull_request(
        client,
        pull_request_payload(
            installation_id=installation_id,
            action="closed",
            title=f"{issue['identifier']}: corrige login",
            state="closed",
            merged=True,
        ),
    )
    after = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}", headers=auth(token)
    )
    activity = await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue['id']}/activity", headers=auth(token)
    )

    assert delivered.json()["data"]["outcome"] == "PROCESSED"
    assert after.json()["data"]["status_id"] == states["Done"]
    assert after.json()["data"]["version"] == issue["version"] + 1
    status_changes = [e for e in activity.json()["data"] if e["action"] == "issue.status_changed"]
    assert len(status_changes) == 1
    assert status_changes[0]["actor_source"] == "GITHUB"
    assert status_changes[0]["actor_id"] is None
    assert status_changes[0]["new_value"] == "Done"
    created_entry = next(e for e in activity.json()["data"] if e["action"] == "issue.created")
    assert created_entry["actor_source"] == "USER"
    assert created_entry["actor_id"] is not None


async def test_rules_can_be_changed_and_cleared(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    states = await _state_ids_by_name(client, workspace_id, token)

    changed = await _set_automation(client, workspace_id, token, "PR_CLOSED", states["Canceled"])
    cleared = await _set_automation(client, workspace_id, token, "PR_MERGED", None)

    assert changed.status_code == 200
    by_event = {rule["event"]: rule["target_state_id"] for rule in cleared.json()["data"]}
    assert by_event == {
        "PR_DRAFT": states["In Progress"],
        "PR_OPEN": states["In Review"],
        "PR_MERGED": None,
        "PR_CLOSED": states["Canceled"],
    }


async def test_rule_cannot_target_a_status_of_another_workspace(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    other_token = await register_and_login(client)
    other_workspace_id = await create_workspace(client, other_token)
    foreign_state = (await _state_ids_by_name(client, other_workspace_id, other_token))["Done"]

    response = await _set_automation(client, workspace_id, token, "PR_MERGED", foreign_state)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "workflow_state_not_found"


async def test_member_cannot_see_or_change_rules(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    member_token = await invite_and_accept(client, workspace_id, token, "MEMBER")

    read = await _automations(client, workspace_id, member_token)
    write = await _set_automation(client, workspace_id, member_token, "PR_MERGED", None)

    assert (read.status_code, write.status_code) == (403, 403)


async def test_deleting_the_target_status_turns_the_rule_into_no_action(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    states = await _state_ids_by_name(client, workspace_id, token)

    deleted = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/workflow-states/{states['In Review']}",
        headers=auth(token),
    )

    assert deleted.status_code == 204
    by_event = {
        rule["event"]: rule["target_state_id"]
        for rule in (await _automations(client, workspace_id, token)).json()["data"]
    }
    assert by_event["PR_OPEN"] is None
    assert by_event["PR_MERGED"] == states["Done"]
