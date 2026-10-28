import uuid
from datetime import UTC, datetime

import pytest

# Mesmo motivo de `test_issue_service.py`: relacionamentos entre features precisam
# estar registrados antes de instanciar models isoladamente.
import src.db.models_registry  # noqa: F401
from src.features.issues.models import ActivityActorSource, Issue, IssuePriority
from src.features.issues.schemas import AutomationActor
from src.features.issues.service import IssueService
from src.features.notifications.models import NotificationType
from src.features.workflow_states.models import WorkflowState
from src.features.workflow_states.service import WorkflowStateService

from tests.unit.features.github.fakes import make_issue_service
from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.notifications.fakes import FakeNotificationRepository
from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository

_GITHUB = AutomationActor(source=ActivityActorSource.GITHUB, user_id=None, name="GitHub")


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def workflow_state_repo() -> FakeWorkflowStateRepository:
    return FakeWorkflowStateRepository()


@pytest.fixture
def notification_repo() -> FakeNotificationRepository:
    return FakeNotificationRepository()


@pytest.fixture
def service(
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
    notification_repo: FakeNotificationRepository,
) -> IssueService:
    return make_issue_service(issue_repo, workflow_state_repo, notification_repo)


@pytest.fixture
async def states(workflow_state_repo: FakeWorkflowStateRepository) -> dict[str, WorkflowState]:
    workspace_id = uuid.uuid4()
    await WorkflowStateService(workflow_state_repo).seed_defaults(workspace_id)
    return {s.name: s for s in await workflow_state_repo.list_by_workspace(workspace_id)}


async def _issue(
    issue_repo: FakeIssueRepository,
    state: WorkflowState,
    *,
    assignee_id: uuid.UUID | None = None,
) -> Issue:
    return await issue_repo.create(
        Issue(
            workspace_id=state.workspace_id,
            number=1,
            title="Corrigir login",
            status_id=state.id,
            priority=IssuePriority.NO_PRIORITY,
            creator_id=uuid.uuid4(),
            assignee_id=assignee_id,
        )
    )


async def test_moves_issue_and_records_github_as_the_author(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    notification_repo: FakeNotificationRepository,
    states: dict[str, WorkflowState],
) -> None:
    assignee_id = uuid.uuid4()
    issue = await _issue(issue_repo, states["In Progress"], assignee_id=assignee_id)

    moved = await service.apply_automation_transition(
        issue.workspace_id, issue.id, states["In Review"].id, _GITHUB
    )

    assert moved is True
    assert issue.status_id == states["In Review"].id
    assert issue.version == 2
    [activity] = issue_repo.activity_log
    assert activity.actor_id is None
    assert activity.actor_source == ActivityActorSource.GITHUB
    assert (activity.action, activity.old_value, activity.new_value) == (
        "issue.status_changed",
        "In Progress",
        "In Review",
    )
    [notification] = notification_repo.notifications.values()
    assert notification.user_id == assignee_id
    assert notification.type == NotificationType.STATUS_CHANGE
    assert notification.payload["actor_name"] == "GitHub"


async def test_mapped_member_is_the_author_and_is_not_notified_about_own_change(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    notification_repo: FakeNotificationRepository,
    states: dict[str, WorkflowState],
) -> None:
    member_id = uuid.uuid4()
    issue = await _issue(issue_repo, states["In Review"], assignee_id=member_id)
    actor = AutomationActor(
        source=ActivityActorSource.GITHUB, user_id=member_id, name="Ada via GitHub"
    )

    await service.apply_automation_transition(
        issue.workspace_id, issue.id, states["Done"].id, actor
    )

    [activity] = issue_repo.activity_log
    assert activity.actor_id == member_id
    assert activity.actor_source == ActivityActorSource.GITHUB
    assert notification_repo.notifications == {}


@pytest.mark.parametrize("terminal", ["Done", "Canceled"])
async def test_completed_or_canceled_issue_is_never_moved(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    states: dict[str, WorkflowState],
    terminal: str,
) -> None:
    """Um PR reaberto ou um segundo PR não desfaz uma conclusão ou um cancelamento."""
    issue = await _issue(issue_repo, states[terminal])

    moved = await service.apply_automation_transition(
        issue.workspace_id, issue.id, states["In Review"].id, _GITHUB
    )

    assert moved is False
    assert issue.status_id == states[terminal].id
    assert issue.version == 1
    assert issue_repo.activity_log == []


async def test_issue_already_in_the_target_status_is_left_alone(
    service: IssueService, issue_repo: FakeIssueRepository, states: dict[str, WorkflowState]
) -> None:
    issue = await _issue(issue_repo, states["In Review"])

    moved = await service.apply_automation_transition(
        issue.workspace_id, issue.id, states["In Review"].id, _GITHUB
    )

    assert moved is False
    assert issue_repo.activity_log == []


async def test_rule_pointing_to_a_deleted_status_does_nothing(
    service: IssueService, issue_repo: FakeIssueRepository, states: dict[str, WorkflowState]
) -> None:
    issue = await _issue(issue_repo, states["Todo"])
    states["In Review"].deleted_at = datetime.now(UTC)

    moved = await service.apply_automation_transition(
        issue.workspace_id, issue.id, states["In Review"].id, _GITHUB
    )

    assert moved is False
    assert issue.status_id == states["Todo"].id


async def test_missing_issue_does_nothing(
    service: IssueService, states: dict[str, WorkflowState]
) -> None:
    moved = await service.apply_automation_transition(
        states["Done"].workspace_id, uuid.uuid4(), states["Done"].id, _GITHUB
    )

    assert moved is False
