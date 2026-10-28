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


async def _create_issue(client: AsyncClient, workspace_id: str, token: str) -> dict:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/issues",
        json={"title": "Corrigir login"},
        headers=auth(token),
    )
    issue: dict = response.json()["data"]
    return issue


async def _links(client: AsyncClient, workspace_id: str, issue_id: str, token: str) -> Response:
    return await client.get(
        f"/api/v1/workspaces/{workspace_id}/issues/{issue_id}/github-links", headers=auth(token)
    )


async def test_pull_request_citing_the_issue_shows_up_on_it(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)
    await return_from_github(client, await connect(client, workspace_id, token), installation_id)
    issue = await _create_issue(client, workspace_id, token)
    branch = f"{issue['identifier'].lower()}-corrigir-login"

    delivered = await _deliver_pull_request(
        client,
        pull_request_payload(installation_id=installation_id, branch=branch, draft=True),
    )
    links = await _links(client, workspace_id, issue["id"], token)

    assert delivered.json()["data"] == {"outcome": "PROCESSED", "duplicate": False}
    assert links.status_code == 200
    [link] = links.json()["data"]
    assert link["repository_full_name"] == "Codertocat/Hello-World"
    assert link["pr_number"] == 2
    assert link["pr_url"] == "https://github.com/Codertocat/Hello-World/pull/2"
    assert link["pr_state"] == "DRAFT"
    assert link["author_login"] == "Codertocat"
    assert link["head_branch"] == branch

    merged = await _deliver_pull_request(
        client,
        pull_request_payload(
            installation_id=installation_id,
            action="closed",
            branch=branch,
            state="closed",
            merged=True,
            updated_at="2019-05-16T10:00:00Z",
        ),
    )
    [after_merge] = (await _links(client, workspace_id, issue["id"], token)).json()["data"]
    assert merged.json()["data"]["outcome"] == "PROCESSED"
    assert after_merge["pr_state"] == "MERGED"


async def test_same_identifier_in_another_workspace_is_not_linked(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    """Os dois workspaces têm uma `FD-1`; só o da instalação recebe o vínculo."""
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)
    await return_from_github(client, await connect(client, workspace_id, token), installation_id)
    issue = await _create_issue(client, workspace_id, token)
    other_token = await register_and_login(client)
    other_workspace_id = await create_workspace(client, other_token)
    other_issue = await _create_issue(client, other_workspace_id, other_token)
    assert issue["identifier"] == other_issue["identifier"]

    await _deliver_pull_request(
        client,
        pull_request_payload(installation_id=installation_id, title=f"{issue['identifier']}"),
    )

    assert len((await _links(client, workspace_id, issue["id"], token)).json()["data"]) == 1
    other_links = await _links(client, other_workspace_id, other_issue["id"], other_token)
    assert other_links.json()["data"] == []


async def test_guest_can_see_links_but_outsider_cannot(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)
    await return_from_github(client, await connect(client, workspace_id, token), installation_id)
    issue = await _create_issue(client, workspace_id, token)
    await _deliver_pull_request(
        client,
        pull_request_payload(installation_id=installation_id, title=issue["identifier"]),
    )
    guest_token = await invite_and_accept(client, workspace_id, token, "GUEST")
    outsider_token = await register_and_login(client)

    as_guest = await _links(client, workspace_id, issue["id"], guest_token)
    as_outsider = await _links(client, workspace_id, issue["id"], outsider_token)

    assert as_guest.status_code == 200
    assert len(as_guest.json()["data"]) == 1
    assert as_outsider.status_code == 404


async def test_links_of_unknown_issue_is_not_found(client: AsyncClient) -> None:
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)

    response = await _links(client, workspace_id, str(uuid.uuid4()), token)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "issue_not_found"
