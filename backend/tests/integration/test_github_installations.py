import secrets
import uuid
from collections.abc import AsyncGenerator

import pytest
from redis.asyncio import Redis, from_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import get_settings
from src.features.auth.models import User
from src.features.github.models import GitHubInstallation
from src.features.github.repository import (
    GitHubConnectIntent,
    GitHubConnectStateRepository,
    GitHubInstallationRepository,
)
from src.features.workspaces.models import Workspace
from src.features.workspaces.repository import WorkspaceRepository
from tests.integration.conftest import unique_suffix


@pytest.fixture
def installation_repo(db_session: AsyncSession) -> GitHubInstallationRepository:
    return GitHubInstallationRepository(db_session)


@pytest.fixture
async def other_workspace(workspace_repo: WorkspaceRepository, user: User) -> Workspace:
    return await workspace_repo.create(
        Workspace(name="Outra", slug=f"outra-{unique_suffix()}", owner_id=user.id)
    )


@pytest.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    client = from_url(get_settings().redis_url, decode_responses=True)
    yield client
    await client.aclose()


def _random_installation_id() -> int:
    """Testes de contrato gravam instalações de verdade no mesmo banco; um id
    aleatório evita colidir com elas no índice único global."""
    return secrets.randbelow(10**12) + 10**9


def _installation(workspace: Workspace, user: User, installation_id: int) -> GitHubInstallation:
    return GitHubInstallation(
        workspace_id=workspace.id,
        installation_id=installation_id,
        account_login="acme-org",
        account_type="Organization",
        connected_by_id=user.id,
    )


async def test_installation_is_unique_across_workspaces_while_active(
    db_session: AsyncSession,
    installation_repo: GitHubInstallationRepository,
    workspace: Workspace,
    other_workspace: Workspace,
    user: User,
) -> None:
    installation_id = _random_installation_id()
    await installation_repo.create(_installation(workspace, user, installation_id))
    db_session.add(_installation(other_workspace, user, installation_id))

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_installation_id_is_free_again_after_soft_delete(
    installation_repo: GitHubInstallationRepository,
    workspace: Workspace,
    other_workspace: Workspace,
    user: User,
) -> None:
    installation_id = _random_installation_id()
    first = await installation_repo.create(_installation(workspace, user, installation_id))
    await installation_repo.soft_delete(workspace.id, first.id)

    second = await installation_repo.create(_installation(other_workspace, user, installation_id))

    found = await installation_repo.get_active_by_installation_id(installation_id)
    assert found is not None
    assert found.id == second.id


async def test_reads_are_scoped_to_workspace_and_skip_deleted(
    installation_repo: GitHubInstallationRepository,
    workspace: Workspace,
    other_workspace: Workspace,
    user: User,
) -> None:
    kept = await installation_repo.create(_installation(workspace, user, _random_installation_id()))
    removed = await installation_repo.create(
        _installation(workspace, user, _random_installation_id())
    )
    await installation_repo.soft_delete(workspace.id, removed.id)

    listed = await installation_repo.list_by_workspace(workspace.id)

    assert [i.id for i in listed] == [kept.id]
    assert await installation_repo.get_by_id(other_workspace.id, kept.id) is None
    assert await installation_repo.get_by_id(workspace.id, removed.id) is None


async def test_soft_delete_ignores_installation_of_another_workspace(
    installation_repo: GitHubInstallationRepository,
    workspace: Workspace,
    other_workspace: Workspace,
    user: User,
) -> None:
    installation = await installation_repo.create(
        _installation(workspace, user, _random_installation_id())
    )

    await installation_repo.soft_delete(other_workspace.id, installation.id)

    assert await installation_repo.get_by_id(workspace.id, installation.id) is not None


async def test_connect_state_is_single_use_and_expires(redis: Redis) -> None:
    repo = GitHubConnectStateRepository(redis)
    state = secrets.token_urlsafe(32)
    intent = GitHubConnectIntent(workspace_id=uuid.uuid4(), user_id=uuid.uuid4())

    await repo.save(state, intent, ttl_seconds=600)
    keys = [key async for key in redis.scan_iter("github:connect:*")]
    ttls = [await redis.ttl(key) for key in keys]

    assert await repo.pop(state) == intent
    assert await repo.pop(state) is None
    assert all(state not in key for key in keys)
    assert all(0 < ttl <= 600 for ttl in ttls)
