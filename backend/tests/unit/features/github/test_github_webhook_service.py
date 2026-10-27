import uuid
from datetime import UTC, datetime

import pytest
from src.features.github.exceptions import GitHubWebhookPayloadInvalidError
from src.features.github.models import GitHubInstallation, GitHubWebhookOutcome
from src.features.github.schemas import GitHubWebhookDeliveryInput
from src.features.github.service import GitHubWebhookService

from tests.github_payloads import load_payload
from tests.unit.features.github.fakes import (
    FakeGitHubInstallationRepository,
    FakeGitHubPullRequestLinkRepository,
    FakeGitHubWebhookDeliveryRepository,
)
from tests.unit.features.issues.fakes import FakeIssueRepository

_INSTALLATION_ID = 4242


@pytest.fixture
def installation_repo() -> FakeGitHubInstallationRepository:
    return FakeGitHubInstallationRepository()


@pytest.fixture
def delivery_repo() -> FakeGitHubWebhookDeliveryRepository:
    return FakeGitHubWebhookDeliveryRepository()


@pytest.fixture
def service(
    installation_repo: FakeGitHubInstallationRepository,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
) -> GitHubWebhookService:
    return GitHubWebhookService(
        installation_repo,
        delivery_repo,
        FakeGitHubPullRequestLinkRepository(),
        FakeIssueRepository(),
    )


@pytest.fixture
async def installation(installation_repo: FakeGitHubInstallationRepository) -> GitHubInstallation:
    return await installation_repo.create(
        GitHubInstallation(
            workspace_id=uuid.uuid4(),
            installation_id=_INSTALLATION_ID,
            account_login="acme-org",
            account_type="Organization",
            connected_by_id=uuid.uuid4(),
        )
    )


def _delivery(
    event: str, fixture: str, *, installation_id: int | None = _INSTALLATION_ID
) -> GitHubWebhookDeliveryInput:
    return GitHubWebhookDeliveryInput.parse(
        delivery_id=str(uuid.uuid4()),
        event=event,
        body=load_payload(fixture, installation_id=installation_id),
    )


async def test_installation_deleted_disconnects_the_workspace(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
) -> None:
    delivery = _delivery("installation", "installation_deleted")

    result = await service.handle(delivery)

    assert result.outcome == GitHubWebhookOutcome.PROCESSED
    assert result.duplicate is False
    assert installation.deleted_at is not None
    recorded = delivery_repo.deliveries[delivery.delivery_id]
    assert recorded.event == "installation"
    assert recorded.action == "deleted"
    assert recorded.installation_id == _INSTALLATION_ID
    assert recorded.workspace_id == installation.workspace_id
    assert recorded.reason is None


async def test_suspend_uses_github_timestamp_and_unsuspend_clears_it(
    service: GitHubWebhookService, installation: GitHubInstallation
) -> None:
    await service.handle(_delivery("installation", "installation_suspend"))
    assert installation.suspended_at == datetime(2021, 4, 29, 2, 32, 50, tzinfo=UTC)

    await service.handle(_delivery("installation", "installation_unsuspend"))
    assert installation.suspended_at is None


async def test_suspend_without_timestamp_falls_back_to_now(
    service: GitHubWebhookService, installation: GitHubInstallation
) -> None:
    delivery = _delivery("installation", "installation_suspend")
    assert delivery.payload.installation is not None
    delivery.payload.installation.suspended_at = None
    before = datetime.now(UTC)

    await service.handle(delivery)

    assert installation.suspended_at is not None
    assert installation.suspended_at >= before


async def test_installation_repositories_is_only_recorded(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
) -> None:
    delivery = _delivery("installation_repositories", "installation_repositories_added")

    result = await service.handle(delivery)

    assert result.outcome == GitHubWebhookOutcome.PROCESSED
    assert installation.deleted_at is None
    assert installation.suspended_at is None
    assert delivery_repo.deliveries[delivery.delivery_id].workspace_id == installation.workspace_id


@pytest.mark.parametrize(
    ("event", "fixture", "installation_id", "reason"),
    [
        ("ping", "ping", None, "unhandled_event"),
        ("issues", "pull_request_opened", _INSTALLATION_ID, "unhandled_event"),
        ("installation", "installation_created", _INSTALLATION_ID, "unhandled_action"),
        ("installation", "installation_deleted", 999, "unknown_installation"),
    ],
)
async def test_events_the_flowdesk_does_not_act_on_are_recorded_as_ignored(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
    event: str,
    fixture: str,
    installation_id: int | None,
    reason: str,
) -> None:
    delivery = _delivery(event, fixture, installation_id=installation_id)

    result = await service.handle(delivery)

    assert result.outcome == GitHubWebhookOutcome.IGNORED
    assert delivery_repo.deliveries[delivery.delivery_id].reason == reason
    assert installation.deleted_at is None


async def test_handled_event_without_installation_is_ignored(
    service: GitHubWebhookService, delivery_repo: FakeGitHubWebhookDeliveryRepository
) -> None:
    delivery = GitHubWebhookDeliveryInput.parse(
        delivery_id="d-1", event="installation", body=b'{"action": "deleted"}'
    )

    result = await service.handle(delivery)

    assert result.outcome == GitHubWebhookOutcome.IGNORED
    assert delivery_repo.deliveries["d-1"].reason == "missing_installation"


async def test_redelivery_returns_first_outcome_without_reapplying_the_effect(
    service: GitHubWebhookService, installation: GitHubInstallation
) -> None:
    """O GitHub reenvia com o mesmo `X-GitHub-Delivery`. Aqui o reenvio carrega outro
    corpo de propósito: se o efeito fosse reaplicado, a instalação voltaria a ativa."""
    suspend = _delivery("installation", "installation_suspend")
    await service.handle(suspend)
    replay = GitHubWebhookDeliveryInput.parse(
        delivery_id=suspend.delivery_id,
        event="installation",
        body=load_payload("installation_unsuspend", installation_id=_INSTALLATION_ID),
    )

    result = await service.handle(replay)

    assert result.duplicate is True
    assert result.outcome == GitHubWebhookOutcome.PROCESSED
    assert installation.suspended_at is not None


@pytest.mark.parametrize(
    ("delivery_id", "event", "body"),
    [
        (None, "installation", b"{}"),
        ("d-1", None, b"{}"),
        ("x" * 65, "installation", b"{}"),
        ("d-1", "e" * 65, b"{}"),
        ("d-1", "installation", b"not json"),
        ("d-1", "installation", b"[]"),
        ("d-1", "installation", b'{"installation": {"id": "abc"}}'),
    ],
    ids=["no-delivery", "no-event", "long-delivery", "long-event", "not-json", "array", "bad-id"],
)
def test_malformed_delivery_is_rejected(
    delivery_id: str | None, event: str | None, body: bytes
) -> None:
    with pytest.raises(GitHubWebhookPayloadInvalidError):
        GitHubWebhookDeliveryInput.parse(delivery_id=delivery_id, event=event, body=body)
