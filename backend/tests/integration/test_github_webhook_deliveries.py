import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.github.models import GitHubWebhookOutcome
from src.features.github.repository import GitHubWebhookDeliveryRepository
from src.features.workspaces.models import Workspace


@pytest.fixture
def delivery_repo(db_session: AsyncSession) -> GitHubWebhookDeliveryRepository:
    return GitHubWebhookDeliveryRepository(db_session)


async def test_delivery_is_claimed_only_once(
    delivery_repo: GitHubWebhookDeliveryRepository,
) -> None:
    delivery_id = str(uuid.uuid4())

    first = await delivery_repo.claim(
        delivery_id=delivery_id, event="installation", action="deleted", installation_id=42
    )
    second = await delivery_repo.claim(
        delivery_id=delivery_id, event="installation", action="suspend", installation_id=42
    )

    assert first is True
    assert second is False
    stored = await delivery_repo.get(delivery_id)
    assert stored is not None
    assert stored.action == "deleted"
    assert stored.received_at is not None


async def test_finish_records_outcome_reason_and_workspace(
    db_session: AsyncSession,
    delivery_repo: GitHubWebhookDeliveryRepository,
    workspace: Workspace,
) -> None:
    delivery_id = str(uuid.uuid4())
    workspace_id = workspace.id
    await delivery_repo.claim(
        delivery_id=delivery_id, event="installation", action="created", installation_id=42
    )

    await delivery_repo.finish(
        delivery_id,
        outcome=GitHubWebhookOutcome.IGNORED,
        reason="unhandled_action",
        workspace_id=workspace_id,
    )

    # Relê do banco: `finish` é um UPDATE em Core, não passa pelo objeto da sessão.
    db_session.expire_all()
    stored = await delivery_repo.get(delivery_id)
    assert stored is not None
    assert stored.outcome == GitHubWebhookOutcome.IGNORED
    assert stored.reason == "unhandled_action"
    assert stored.workspace_id == workspace_id


async def test_delivery_without_installation_is_accepted(
    delivery_repo: GitHubWebhookDeliveryRepository,
) -> None:
    delivery_id = str(uuid.uuid4())

    assert await delivery_repo.claim(
        delivery_id=delivery_id, event="ping", action=None, installation_id=None
    )
    stored = await delivery_repo.get(delivery_id)
    assert stored is not None
    assert stored.installation_id is None
    assert stored.workspace_id is None
