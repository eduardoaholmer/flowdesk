import uuid

import pytest
from src.core.authorization import PermissionService
from src.features.github.models import (
    GitHubAutomationEvent,
    GitHubInstallation,
    GitHubWebhookOutcome,
)
from src.features.github.repository import GitHubSenderMember
from src.features.github.schemas import GitHubWebhookDeliveryInput
from src.features.github.service import (
    GitHubIntegrationService,
    GitHubWebhookService,
    default_automation_targets,
)
from src.features.issues.models import ActivityActorSource, Issue, IssuePriority
from src.features.workflow_states.exceptions import WorkflowStateNotFoundError
from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory
from src.features.workflow_states.service import WorkflowStateService

from tests.github_payloads import pull_request_payload
from tests.unit.features.github.fakes import (
    FakeGitHubConnectStateRepository,
    FakeGitHubInstallationRepository,
    FakeGitHubPullRequestLinkRepository,
    FakeGitHubSenderRepository,
    FakeGitHubStatusAutomationRepository,
    FakeGitHubWebhookDeliveryRepository,
    make_issue_service,
)
from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.permissions.fakes import FakePermissionOverrideRepository
from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository
from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository

_INSTALLATION_ID = 4242
# `sender.id` do payload real de `pull_request/opened` (`Codertocat`).
_SENDER_ID = 21031067


@pytest.fixture
def workflow_state_repo() -> FakeWorkflowStateRepository:
    return FakeWorkflowStateRepository()


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def automation_repo() -> FakeGitHubStatusAutomationRepository:
    return FakeGitHubStatusAutomationRepository()


@pytest.fixture
def sender_repo() -> FakeGitHubSenderRepository:
    return FakeGitHubSenderRepository()


@pytest.fixture
def installation_repo() -> FakeGitHubInstallationRepository:
    return FakeGitHubInstallationRepository()


@pytest.fixture
def service(
    installation_repo: FakeGitHubInstallationRepository,
    issue_repo: FakeIssueRepository,
    automation_repo: FakeGitHubStatusAutomationRepository,
    sender_repo: FakeGitHubSenderRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> GitHubWebhookService:
    return GitHubWebhookService(
        installation_repo,
        FakeGitHubWebhookDeliveryRepository(),
        FakeGitHubPullRequestLinkRepository(),
        issue_repo,
        automation_repo,
        sender_repo,
        make_issue_service(issue_repo, workflow_state_repo),
    )


@pytest.fixture
async def workspace_id(
    installation_repo: FakeGitHubInstallationRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
    automation_repo: FakeGitHubStatusAutomationRepository,
) -> uuid.UUID:
    """Workspace conectado, com os status do seed e as regras padrão gravadas."""
    workspace_id = uuid.uuid4()
    await WorkflowStateService(workflow_state_repo).seed_defaults(workspace_id)
    await installation_repo.create(
        GitHubInstallation(
            workspace_id=workspace_id,
            installation_id=_INSTALLATION_ID,
            account_login="Codertocat",
            account_type="User",
            connected_by_id=uuid.uuid4(),
        )
    )
    states = await workflow_state_repo.list_by_workspace(workspace_id)
    for event, target in default_automation_targets(states).items():
        await automation_repo.upsert(workspace_id, event, target)
    return workspace_id


async def _states(
    workflow_state_repo: FakeWorkflowStateRepository, workspace_id: uuid.UUID
) -> dict[str, WorkflowState]:
    return {s.name: s for s in await workflow_state_repo.list_by_workspace(workspace_id)}


async def _issue(issue_repo: FakeIssueRepository, state: WorkflowState, number: int = 1) -> Issue:
    return await issue_repo.create(
        Issue(
            workspace_id=state.workspace_id,
            number=number,
            title=f"Issue {number}",
            status_id=state.id,
            priority=IssuePriority.NO_PRIORITY,
            creator_id=uuid.uuid4(),
        )
    )


async def _deliver(service: GitHubWebhookService, **overrides: object) -> GitHubWebhookOutcome:
    delivery = GitHubWebhookDeliveryInput.parse(
        delivery_id=str(uuid.uuid4()),
        event="pull_request",
        body=pull_request_payload(installation_id=_INSTALLATION_ID, **overrides),  # type: ignore[arg-type]
    )
    return (await service.handle(delivery)).outcome


async def test_pull_request_lifecycle_moves_the_issue_through_the_board(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)
    issue = await _issue(issue_repo, states["Todo"])

    await _deliver(service, branch="fd-1-login", draft=True, updated_at="2026-10-27T10:00:00Z")
    after_draft = issue.status_id
    await _deliver(
        service, action="ready_for_review", branch="fd-1-login", updated_at="2026-10-27T11:00:00Z"
    )
    after_ready = issue.status_id
    await _deliver(
        service,
        action="closed",
        branch="fd-1-login",
        state="closed",
        merged=True,
        updated_at="2026-10-27T12:00:00Z",
    )

    assert after_draft == states["In Progress"].id
    assert after_ready == states["In Review"].id
    assert issue.status_id == states["Done"].id
    assert [a.new_value for a in issue_repo.activity_log] == ["In Progress", "In Review", "Done"]
    assert {a.actor_source for a in issue_repo.activity_log} == {ActivityActorSource.GITHUB}
    assert {a.actor_id for a in issue_repo.activity_log} == {None}


async def test_member_who_signed_in_with_the_same_github_account_is_the_author(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
    sender_repo: FakeGitHubSenderRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)
    issue = await _issue(issue_repo, states["Todo"])
    member = GitHubSenderMember(user_id=uuid.uuid4(), name="Ada")
    sender_repo.members[(workspace_id, _SENDER_ID)] = member

    await _deliver(service, title="FD-1")

    assert issue.status_id == states["In Review"].id
    [activity] = issue_repo.activity_log
    assert activity.actor_id == member.user_id
    assert activity.actor_source == ActivityActorSource.GITHUB


async def test_closing_without_merge_does_nothing_by_default(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)
    issue = await _issue(issue_repo, states["In Review"])

    outcome = await _deliver(service, action="closed", title="FD-1", state="closed", merged=False)

    assert outcome == GitHubWebhookOutcome.PROCESSED
    assert issue.status_id == states["In Review"].id
    assert issue_repo.activity_log == []


async def test_editing_applies_the_rule_only_to_newly_cited_issues(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    """Quem moveu a issue já vinculada à mão não a vê voltar por causa de uma edição
    no título do PR; a issue que passou a ser citada entra no fluxo."""
    states = await _states(workflow_state_repo, workspace_id)
    first = await _issue(issue_repo, states["Todo"], number=1)
    second = await _issue(issue_repo, states["Todo"], number=2)
    await _deliver(service, title="FD-1", updated_at="2026-10-27T10:00:00Z")
    first.status_id = states["In Progress"].id

    await _deliver(service, action="edited", title="FD-1 e FD-2", updated_at="2026-10-27T11:00:00Z")

    assert first.status_id == states["In Progress"].id
    assert second.status_id == states["In Review"].id


async def test_stale_event_never_moves_an_issue(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)
    issue = await _issue(issue_repo, states["Todo"])
    await _deliver(
        service,
        action="closed",
        title="FD-1",
        state="closed",
        merged=True,
        updated_at="2026-10-27T12:00:00Z",
    )

    await _deliver(service, action="reopened", title="FD-1", updated_at="2026-10-27T09:00:00Z")

    assert issue.status_id == states["Done"].id


async def test_rule_set_to_no_action_is_respected(
    service: GitHubWebhookService,
    workspace_id: uuid.UUID,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
    automation_repo: FakeGitHubStatusAutomationRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)
    issue = await _issue(issue_repo, states["Todo"])
    await automation_repo.upsert(workspace_id, GitHubAutomationEvent.PR_OPEN, None)

    await _deliver(service, title="FD-1")

    assert issue.status_id == states["Todo"].id


def _state(category: WorkflowStateCategory, position: int) -> WorkflowState:
    return WorkflowState(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name=f"{category}-{position}",
        category=category,
        position=position,
        is_default=False,
    )


def test_defaults_follow_board_position_not_names() -> None:
    review = _state(WorkflowStateCategory.STARTED, 3)
    doing = _state(WorkflowStateCategory.STARTED, 2)
    shipped = _state(WorkflowStateCategory.COMPLETED, 5)
    verified = _state(WorkflowStateCategory.COMPLETED, 6)
    backlog = _state(WorkflowStateCategory.BACKLOG, 0)

    targets = default_automation_targets([verified, review, backlog, shipped, doing])

    assert targets == {
        GitHubAutomationEvent.PR_DRAFT: doing.id,
        GitHubAutomationEvent.PR_OPEN: review.id,
        GitHubAutomationEvent.PR_MERGED: shipped.id,
        GitHubAutomationEvent.PR_CLOSED: None,
    }


def test_defaults_without_started_or_completed_status_are_no_action() -> None:
    targets = default_automation_targets([_state(WorkflowStateCategory.BACKLOG, 0)])

    assert set(targets.values()) == {None}


@pytest.fixture
def integration_service(
    workflow_state_repo: FakeWorkflowStateRepository,
    automation_repo: FakeGitHubStatusAutomationRepository,
) -> GitHubIntegrationService:
    return GitHubIntegrationService(
        FakeGitHubInstallationRepository(),
        FakeGitHubConnectStateRepository(),
        FakeWorkspaceRepository(),
        FakePermissionOverrideRepository(),
        PermissionService(),
        automation_repo,
        workflow_state_repo,
        None,
    )


async def test_rules_list_always_has_the_four_events(
    integration_service: GitHubIntegrationService,
) -> None:
    rules = await integration_service.list_automations(uuid.uuid4())

    assert [rule.event for rule in rules] == list(GitHubAutomationEvent)
    assert {rule.target_state_id for rule in rules} == {None}


async def test_rule_can_be_changed_or_cleared(
    integration_service: GitHubIntegrationService,
    workspace_id: uuid.UUID,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    states = await _states(workflow_state_repo, workspace_id)

    changed = await integration_service.set_automation(
        workspace_id, GitHubAutomationEvent.PR_CLOSED, states["Canceled"].id
    )
    cleared = await integration_service.set_automation(
        workspace_id, GitHubAutomationEvent.PR_MERGED, None
    )

    by_event = {rule.event: rule.target_state_id for rule in cleared}
    assert {rule.event: rule.target_state_id for rule in changed}[
        GitHubAutomationEvent.PR_CLOSED
    ] == states["Canceled"].id
    assert by_event[GitHubAutomationEvent.PR_MERGED] is None
    assert by_event[GitHubAutomationEvent.PR_OPEN] == states["In Review"].id


async def test_rule_cannot_point_to_a_status_of_another_workspace(
    integration_service: GitHubIntegrationService,
    workspace_id: uuid.UUID,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    other_workspace_id = uuid.uuid4()
    await WorkflowStateService(workflow_state_repo).seed_defaults(other_workspace_id)
    foreign_state = (await workflow_state_repo.list_by_workspace(other_workspace_id))[0]

    with pytest.raises(WorkflowStateNotFoundError):
        await integration_service.set_automation(
            workspace_id, GitHubAutomationEvent.PR_OPEN, foreign_state.id
        )
