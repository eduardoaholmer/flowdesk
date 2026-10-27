import uuid
from datetime import UTC, datetime

import pytest
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.permissions import Permission
from src.features.github.client import GitHubInstallationInfo
from src.features.github.exceptions import (
    GitHubAuthorizationFailedError,
    GitHubConnectStateInvalidError,
    GitHubInstallationAlreadyConnectedError,
    GitHubInstallationNotAccessibleError,
    GitHubInstallationNotFoundError,
    GitHubInstallationPendingApprovalError,
    GitHubIntegrationNotConfiguredError,
)
from src.features.github.models import GitHubInstallation
from src.features.github.service import CONNECT_STATE_TTL_SECONDS, GitHubIntegrationService
from src.features.permissions.models import PermissionOverride
from src.features.workspaces.exceptions import WorkspaceNotFoundError
from src.features.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole

from tests.unit.features.github.fakes import (
    FakeGitHubAppClient,
    FakeGitHubConnectStateRepository,
    FakeGitHubInstallationRepository,
)
from tests.unit.features.permissions.fakes import FakePermissionOverrideRepository
from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository

_INSTALLATION = GitHubInstallationInfo(
    installation_id=4242, account_login="acme-org", account_type="Organization", suspended_at=None
)


@pytest.fixture
def installation_repo() -> FakeGitHubInstallationRepository:
    return FakeGitHubInstallationRepository()


@pytest.fixture
def state_repo() -> FakeGitHubConnectStateRepository:
    return FakeGitHubConnectStateRepository()


@pytest.fixture
def workspace_repo() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def override_repo() -> FakePermissionOverrideRepository:
    return FakePermissionOverrideRepository()


@pytest.fixture
def client() -> FakeGitHubAppClient:
    return FakeGitHubAppClient([_INSTALLATION])


@pytest.fixture
def service(
    installation_repo: FakeGitHubInstallationRepository,
    state_repo: FakeGitHubConnectStateRepository,
    workspace_repo: FakeWorkspaceRepository,
    override_repo: FakePermissionOverrideRepository,
    client: FakeGitHubAppClient,
) -> GitHubIntegrationService:
    return GitHubIntegrationService(
        installation_repo, state_repo, workspace_repo, override_repo, PermissionService(), client
    )


async def _create_workspace_with_member(
    workspace_repo: FakeWorkspaceRepository, role: WorkspaceRole = WorkspaceRole.ADMIN
) -> tuple[uuid.UUID, WorkspaceMember]:
    owner_id = uuid.uuid4()
    workspace = await workspace_repo.create(Workspace(name="Acme", slug="acme", owner_id=owner_id))
    member = await workspace_repo.add_member(
        WorkspaceMember(workspace_id=workspace.id, user_id=uuid.uuid4(), role=role)
    )
    return workspace.id, member


async def _start(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> tuple[uuid.UUID, WorkspaceMember, str]:
    workspace_id, member = await _create_workspace_with_member(workspace_repo)
    connection = await service.start_connection(workspace_id, member.user_id)
    return workspace_id, member, connection.state


async def _complete(
    service: GitHubIntegrationService,
    state: str,
    *,
    browser_state: str | None = None,
    code: str | None = "github-code",
    installation_id: str | None = "4242",
    setup_action: str | None = "install",
) -> GitHubInstallation:
    return await service.complete_connection(
        state=state,
        browser_state=state if browser_state is None else browser_state,
        code=code,
        installation_id=installation_id,
        setup_action=setup_action,
    )


async def test_start_connection_saves_intent_and_returns_install_url_with_state(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    state_repo: FakeGitHubConnectStateRepository,
) -> None:
    workspace_id, member = await _create_workspace_with_member(workspace_repo)

    connection = await service.start_connection(workspace_id, member.user_id)

    assert f"state={connection.state}" in connection.install_url
    intent = state_repo.states[connection.state]
    assert intent.workspace_id == workspace_id
    assert intent.user_id == member.user_id
    assert state_repo.ttls[connection.state] == CONNECT_STATE_TTL_SECONDS


async def test_start_connection_fails_when_app_not_configured(
    installation_repo: FakeGitHubInstallationRepository,
    state_repo: FakeGitHubConnectStateRepository,
    workspace_repo: FakeWorkspaceRepository,
    override_repo: FakePermissionOverrideRepository,
) -> None:
    service = GitHubIntegrationService(
        installation_repo, state_repo, workspace_repo, override_repo, PermissionService(), None
    )

    with pytest.raises(GitHubIntegrationNotConfiguredError):
        await service.start_connection(uuid.uuid4(), uuid.uuid4())
    assert state_repo.states == {}


async def test_complete_connection_creates_installation_for_the_intent_workspace(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    workspace_id, member, state = await _start(service, workspace_repo)

    installation = await _complete(service, state)

    assert installation.workspace_id == workspace_id
    assert installation.installation_id == 4242
    assert installation.account_login == "acme-org"
    assert installation.account_type == "Organization"
    assert installation.connected_by_id == member.user_id
    status = await service.get_status(workspace_id)
    assert status.configured is True
    assert [i.id for i in status.installations] == [installation.id]


@pytest.mark.parametrize("browser_state", ["", "state-from-another-browser"])
async def test_complete_connection_requires_the_cookie_of_the_browser_that_started_it(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    client: FakeGitHubAppClient,
    browser_state: str,
) -> None:
    """Sem esta checagem, alguém poderia gerar um `state` para o próprio workspace e
    mandar o link de instalação para o dono de outra organização concluir."""
    _, _, state = await _start(service, workspace_repo)

    with pytest.raises(GitHubConnectStateInvalidError):
        await _complete(service, state, browser_state=browser_state)
    assert client.codes == []


async def test_complete_connection_rejects_unknown_or_expired_state(
    service: GitHubIntegrationService, client: FakeGitHubAppClient
) -> None:
    with pytest.raises(GitHubConnectStateInvalidError):
        await _complete(service, "state-never-issued")
    assert client.codes == []


async def test_state_is_single_use(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    _, _, state = await _start(service, workspace_repo)
    await _complete(service, state)

    with pytest.raises(GitHubConnectStateInvalidError):
        await _complete(service, state)


async def test_installation_request_pending_owner_approval_is_reported(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    installation_repo: FakeGitHubInstallationRepository,
) -> None:
    _, _, state = await _start(service, workspace_repo)

    with pytest.raises(GitHubInstallationPendingApprovalError):
        await _complete(service, state, installation_id=None, setup_action="request")
    assert installation_repo.installations == {}


@pytest.mark.parametrize(
    ("code", "installation_id"),
    [
        (None, "4242"),
        ("github-code", None),
        ("github-code", "abc"),
        ("github-code", "-1"),
        ("github-code", "²"),
        ("github-code", "9" * 19),
    ],
)
async def test_complete_connection_rejects_missing_or_malformed_return_params(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    client: FakeGitHubAppClient,
    code: str | None,
    installation_id: str | None,
) -> None:
    _, _, state = await _start(service, workspace_repo)

    with pytest.raises(GitHubAuthorizationFailedError):
        await _complete(service, state, code=code, installation_id=installation_id)
    assert client.codes == []


async def test_installation_outside_the_user_installations_is_refused(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    installation_repo: FakeGitHubInstallationRepository,
) -> None:
    """Trocar o `installation_id` da URL de retorno pelo de outra organização não
    pode ligar essa organização ao workspace (ADR-068)."""
    _, _, state = await _start(service, workspace_repo)

    with pytest.raises(GitHubInstallationNotAccessibleError):
        await _complete(service, state, installation_id="9999")
    assert installation_repo.installations == {}


async def test_installation_connected_to_another_workspace_conflicts(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    _, _, first_state = await _start(service, workspace_repo)
    await _complete(service, first_state)
    _, _, second_state = await _start(service, workspace_repo)

    with pytest.raises(GitHubInstallationAlreadyConnectedError):
        await _complete(service, second_state)


async def test_installation_of_a_deleted_workspace_can_be_connected_elsewhere(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    installation_repo: FakeGitHubInstallationRepository,
) -> None:
    first_workspace_id, _, first_state = await _start(service, workspace_repo)
    first = await _complete(service, first_state)
    await workspace_repo.soft_delete(first_workspace_id)
    second_workspace_id, _, second_state = await _start(service, workspace_repo)

    second = await _complete(service, second_state)

    assert second.workspace_id == second_workspace_id
    assert first.deleted_at is not None
    assert await installation_repo.get_active_by_installation_id(4242) is second


async def test_reconnecting_to_the_same_workspace_updates_instead_of_duplicating(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    installation_repo: FakeGitHubInstallationRepository,
    client: FakeGitHubAppClient,
) -> None:
    workspace_id, member, state = await _start(service, workspace_repo)
    first = await _complete(service, state)
    suspended_at = datetime(2026, 10, 1, tzinfo=UTC)
    client.installations = [
        GitHubInstallationInfo(
            installation_id=4242,
            account_login="acme-renamed",
            account_type="Organization",
            suspended_at=suspended_at,
        )
    ]
    second_state = (await service.start_connection(workspace_id, member.user_id)).state

    second = await _complete(service, second_state, setup_action="update")

    assert second.id == first.id
    assert second.account_login == "acme-renamed"
    assert second.suspended_at == suspended_at
    assert len(installation_repo.installations) == 1


async def test_reconnecting_after_disconnect_creates_a_new_connection(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    workspace_id, member, state = await _start(service, workspace_repo)
    first = await _complete(service, state)
    await service.disconnect(workspace_id, first.id)
    second_state = (await service.start_connection(workspace_id, member.user_id)).state

    second = await _complete(service, second_state)

    assert second.id != first.id
    status = await service.get_status(workspace_id)
    assert [i.id for i in status.installations] == [second.id]


async def test_permission_is_checked_again_when_the_user_returns_from_github(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    client: FakeGitHubAppClient,
) -> None:
    """O `state` vale por 10 minutos; rebaixar o ADMIN nesse meio-tempo precisa
    valer também no retorno."""
    _, member, state = await _start(service, workspace_repo)
    member.role = WorkspaceRole.MEMBER

    with pytest.raises(PermissionDeniedError):
        await _complete(service, state)
    assert client.codes == []


async def test_removed_member_cannot_complete_connection(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    _, member, state = await _start(service, workspace_repo)
    member.deleted_at = datetime.now(UTC)

    with pytest.raises(WorkspaceNotFoundError):
        await _complete(service, state)


async def test_permission_overrides_apply_to_the_return_check(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    override_repo: FakePermissionOverrideRepository,
) -> None:
    workspace_id, member, state = await _start(service, workspace_repo)
    await override_repo.create(
        PermissionOverride(
            workspace_id=workspace_id,
            role=WorkspaceRole.ADMIN,
            permission=Permission.WORKSPACE_MANAGE_INTEGRATIONS,
            granted=False,
        )
    )

    with pytest.raises(PermissionDeniedError):
        await _complete(service, state)


async def test_member_with_granted_override_can_complete_connection(
    service: GitHubIntegrationService,
    workspace_repo: FakeWorkspaceRepository,
    override_repo: FakePermissionOverrideRepository,
) -> None:
    workspace_id, member = await _create_workspace_with_member(workspace_repo, WorkspaceRole.MEMBER)
    await override_repo.create(
        PermissionOverride(
            workspace_id=workspace_id,
            role=WorkspaceRole.MEMBER,
            permission=Permission.WORKSPACE_MANAGE_INTEGRATIONS,
            granted=True,
        )
    )
    state = (await service.start_connection(workspace_id, member.user_id)).state

    installation = await _complete(service, state)

    assert installation.connected_by_id == member.user_id


async def test_disconnect_only_finds_installations_of_the_given_workspace(
    service: GitHubIntegrationService, workspace_repo: FakeWorkspaceRepository
) -> None:
    workspace_id, _, state = await _start(service, workspace_repo)
    installation = await _complete(service, state)
    other_workspace_id, _ = await _create_workspace_with_member(workspace_repo)

    with pytest.raises(GitHubInstallationNotFoundError):
        await service.disconnect(other_workspace_id, installation.id)

    await service.disconnect(workspace_id, installation.id)
    assert (await service.get_status(workspace_id)).installations == []
    with pytest.raises(GitHubInstallationNotFoundError):
        await service.disconnect(workspace_id, installation.id)
