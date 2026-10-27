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
from tests.github_payloads import load_payload, sign
from tests.unit.features.github.fakes import FakeGitHubAppClient

_SECRET = "contract-webhook-secret"
_WEBHOOK_URL = "/api/v1/webhooks/github"


@pytest.fixture
def webhook_settings() -> Iterator[Settings]:
    settings = get_settings().model_copy(update={"github_webhook_secret": _SECRET})
    app.dependency_overrides[get_settings] = lambda: settings
    yield settings
    app.dependency_overrides.pop(get_settings, None)


async def _deliver(
    client: AsyncClient,
    event: str,
    body: bytes,
    *,
    delivery_id: str | None = None,
    signature: str | None = None,
) -> Response:
    return await client.post(
        _WEBHOOK_URL,
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": event,
            "X-GitHub-Delivery": delivery_id or str(uuid.uuid4()),
            "X-Hub-Signature-256": signature if signature is not None else sign(_SECRET, body),
        },
    )


async def _connected_workspace(client: AsyncClient, installation_id: int) -> tuple[str, str]:
    token = await register_and_login(client)
    workspace_id = await create_workspace(client, token)
    await return_from_github(client, await connect(client, workspace_id, token), installation_id)
    return workspace_id, token


async def _installations(client: AsyncClient, workspace_id: str, token: str) -> list[dict]:
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/integrations/github", headers=auth(token)
    )
    installations: list[dict] = response.json()["data"]["installations"]
    return installations


async def test_installation_deleted_on_github_disconnects_the_workspace(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    assert len(await _installations(client, workspace_id, token)) == 1

    response = await _deliver(
        client,
        "installation",
        load_payload("installation_deleted", installation_id=installation_id),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"outcome": "PROCESSED", "duplicate": False}
    assert await _installations(client, workspace_id, token) == []


async def test_suspend_and_unsuspend_are_reflected_on_the_connection(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)

    await _deliver(
        client,
        "installation",
        load_payload("installation_suspend", installation_id=installation_id),
    )
    [suspended] = await _installations(client, workspace_id, token)
    await _deliver(
        client,
        "installation",
        load_payload("installation_unsuspend", installation_id=installation_id),
    )
    [unsuspended] = await _installations(client, workspace_id, token)

    assert suspended["suspended_at"] == "2021-04-29T02:32:50Z"
    assert unsuspended["suspended_at"] is None


async def test_redelivery_does_not_reapply_the_effect(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)
    delivery_id = str(uuid.uuid4())
    await _deliver(
        client,
        "installation",
        load_payload("installation_suspend", installation_id=installation_id),
        delivery_id=delivery_id,
    )

    replay = await _deliver(
        client,
        "installation",
        load_payload("installation_unsuspend", installation_id=installation_id),
        delivery_id=delivery_id,
    )

    assert replay.status_code == 200
    assert replay.json()["data"] == {"outcome": "PROCESSED", "duplicate": True}
    [installation] = await _installations(client, workspace_id, token)
    assert installation["suspended_at"] is not None


@pytest.mark.parametrize(
    ("event", "fixture"),
    [("ping", "ping"), ("pull_request", "pull_request_opened")],
)
async def test_events_not_acted_on_are_acknowledged_as_ignored(
    client: AsyncClient, webhook_settings: Settings, event: str, fixture: str
) -> None:
    response = await _deliver(client, event, load_payload(fixture))

    assert response.status_code == 200
    assert response.json()["data"] == {"outcome": "IGNORED", "duplicate": False}


async def test_installation_never_connected_here_is_ignored(
    client: AsyncClient, webhook_settings: Settings, installation_id: int
) -> None:
    response = await _deliver(
        client,
        "installation",
        load_payload("installation_deleted", installation_id=installation_id),
    )

    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "IGNORED"


@pytest.mark.parametrize(
    "signature",
    ["", "sha256=" + "0" * 64, sign("another-secret", b"{}")],
    ids=["missing", "wrong-digest", "wrong-secret"],
)
async def test_invalid_signature_is_rejected_without_touching_the_connection(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
    signature: str,
) -> None:
    workspace_id, token = await _connected_workspace(client, installation_id)

    response = await _deliver(
        client,
        "installation",
        load_payload("installation_deleted", installation_id=installation_id),
        signature=signature,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_signature"
    assert len(await _installations(client, workspace_id, token)) == 1


async def test_every_delivery_is_rejected_when_no_secret_is_configured(
    client: AsyncClient,
) -> None:
    body = load_payload("ping")

    response = await _deliver(client, "ping", body, signature=sign("anything", body))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_signature"


async def test_body_above_limit_is_rejected_before_the_signature(
    client: AsyncClient, webhook_settings: Settings
) -> None:
    app.dependency_overrides[get_settings] = lambda: webhook_settings.model_copy(
        update={"github_webhook_max_body_bytes": 512}
    )
    body = load_payload("pull_request_opened")
    assert len(body) > 512

    response = await _deliver(client, "pull_request", body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "github_webhook_payload_too_large"


async def test_signed_delivery_without_github_headers_is_rejected(
    client: AsyncClient, webhook_settings: Settings
) -> None:
    body = load_payload("ping")

    response = await client.post(
        _WEBHOOK_URL,
        content=body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sign(_SECRET, body)},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_webhook_payload"


async def test_deliveries_are_counted_by_event_and_outcome(
    client: AsyncClient,
    webhook_settings: Settings,
    github_client: FakeGitHubAppClient,
    installation_id: int,
) -> None:
    await _connected_workspace(client, installation_id)
    delivery_id = str(uuid.uuid4())
    suspend = load_payload("installation_suspend", installation_id=installation_id)
    await _deliver(client, "installation", suspend, delivery_id=delivery_id)
    await _deliver(client, "installation", suspend, delivery_id=delivery_id)
    await _deliver(client, "ping", load_payload("ping"))
    await _deliver(client, "issues", b"{}")

    counters = (await client.get("/metrics")).json()["counters"]

    assert counters == {
        "github_webhook.installation.DUPLICATE": 1,
        "github_webhook.installation.PROCESSED": 1,
        "github_webhook.other.IGNORED": 2,
    }


async def test_member_granted_manage_integrations_by_override_can_connect(
    client: AsyncClient, github_client: FakeGitHubAppClient
) -> None:
    """A permissão nova da Sprint 10.1 também é customizável pela matriz de overrides
    (a coluna `permission_overrides.permission` aceita o valor novo)."""
    owner_token = await register_and_login(client)
    workspace_id = await create_workspace(client, owner_token)
    member_token = await invite_and_accept(client, workspace_id, owner_token, "MEMBER")
    granted = await client.put(
        f"/api/v1/workspaces/{workspace_id}/permission-overrides",
        json={"role": "MEMBER", "permission": "workspace.manage_integrations", "granted": True},
        headers=auth(owner_token),
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/integrations/github/connect",
        headers=auth(member_token),
    )

    assert granted.status_code == 200
    assert response.status_code == 200
