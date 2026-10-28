import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient

from tests.contract.github_support import (
    auth,
    connect,
    create_workspace,
    invite_and_accept,
    register_and_login,
    return_from_github,
)
from tests.unit.features.github.fakes import FakeGitHubAppClient


async def test_status_reports_integration_off_when_app_not_configured(
    client: AsyncClient,
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)

    status = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    connect = await client.post(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/connect",
        headers=auth(owner_token),
    )

    assert status.status_code == 200
    assert status.json()["data"] == {"configured": False, "installations": []}
    assert connect.status_code == 422
    assert connect.json()["error"]["code"] == "github_integration_not_configured"


async def test_full_connection_flow_links_installation_to_workspace(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)

    connect = await client.post(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/connect",
        headers=auth(owner_token),
    )
    install_url = connect.json()["data"]["install_url"]
    assert install_url.startswith("https://github.com/apps/flowdesk-test/installations/new?")
    set_cookie = connect.headers["set-cookie"].lower()
    assert "github_connect_state=" in set_cookie
    assert "path=/api/v1/integrations/github" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    state = parse_qs(urlparse(install_url).query)["state"][0]
    status_code, location = await return_from_github(client, state, installation_id)

    assert status_code == 302
    assert location == "http://localhost:5173/integrations/github/callback"
    assert github_client.codes == ["github-code"]
    status = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    data = status.json()["data"]
    assert data["configured"] is True
    [installation] = data["installations"]
    assert installation["installation_id"] == installation_id
    assert installation["account_login"] == "acme-org"
    assert installation["account_type"] == "Organization"


async def test_return_without_the_browser_cookie_is_refused(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    state = await connect(client, workspace_id, owner_token)
    client.cookies.clear()

    status_code, location = await return_from_github(client, state, installation_id)

    assert status_code == 302
    assert location.endswith("/integrations/github/callback?error=github_connect_state_invalid")
    assert github_client.codes == []


async def test_installation_the_user_cannot_see_is_refused(
    client: AsyncClient, github_client: FakeGitHubAppClient
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    state = await connect(client, workspace_id, owner_token)

    _, location = await return_from_github(client, state, 1)

    assert location.endswith("?error=github_installation_not_accessible")
    status = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    assert status.json()["data"]["installations"] == []


async def test_installation_already_linked_to_another_workspace_is_refused(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    first_token = await register_and_login(client)
    first_workspace = await create_workspace(client, first_token)
    await return_from_github(
        client, await connect(client, first_workspace, first_token), installation_id
    )
    second_token = await register_and_login(client)
    second_workspace = await create_workspace(client, second_token)
    state = await connect(client, second_workspace, second_token)

    _, location = await return_from_github(client, state, installation_id)

    assert location.endswith("?error=github_installation_already_connected")


async def test_disconnect_removes_installation_from_the_workspace(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    await return_from_github(
        client, await connect(client, workspace_id, owner_token), installation_id
    )
    status = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    installation_pk = status.json()["data"]["installations"][0]["id"]

    deleted = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/installations/{installation_pk}",
        headers=auth(owner_token),
    )
    deleted_again = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/installations/{installation_pk}",
        headers=auth(owner_token),
    )

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert deleted_again.json()["error"]["code"] == "github_installation_not_found"
    after = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    assert after.json()["data"]["installations"] == []


async def test_admin_can_manage_integrations(
    client: AsyncClient, github_client: FakeGitHubAppClient
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    admin_token = await invite_and_accept(client, workspace_id, owner_token, "ADMIN")

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/connect",
        headers=auth(admin_token),
    )

    assert response.status_code == 200


@pytest.mark.parametrize("role", ["MEMBER", "GUEST"])
async def test_member_and_guest_cannot_manage_integrations(
    client: AsyncClient, github_client: FakeGitHubAppClient, role: str
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    token = await invite_and_accept(client, workspace_id, owner_token, role)
    base = f"/api/v1/workspaces/{workspace_id}/integrations/github"

    responses = [
        await client.get(base, headers=auth(token)),
        await client.post(f"{base}/connect", headers=auth(token)),
        await client.delete(f"{base}/installations/{uuid.uuid4()}", headers=auth(token)),
    ]

    assert [r.status_code for r in responses] == [403, 403, 403]


async def test_non_member_gets_not_found_and_cannot_touch_another_workspace(
    client: AsyncClient, github_client: FakeGitHubAppClient, installation_id: int
) -> None:
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    await return_from_github(
        client, await connect(client, workspace_id, owner_token), installation_id
    )
    status = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    installation_pk = status.json()["data"]["installations"][0]["id"]
    outsider_token = await register_and_login(client)
    outsider_workspace = await create_workspace(client, outsider_token)

    as_outsider = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(outsider_token)
    )
    cross_tenant_delete = await client.delete(
        f"/api/v1/workspaces/{outsider_workspace}/integrations/github/installations/{installation_pk}",
        headers=auth(outsider_token),
    )

    assert as_outsider.status_code == 404
    assert cross_tenant_delete.status_code == 404
    still_there = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(owner_token)
    )
    assert len(still_there.json()["data"]["installations"]) == 1
