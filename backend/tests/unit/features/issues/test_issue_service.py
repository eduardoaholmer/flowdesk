import uuid
from datetime import date

import pytest

# Garante que os relacionamentos entre features (`Project.issues` -> `Issue`,
# `Issue.comments` -> `Comment`) estejam resolvíveis antes de instanciar
# models isoladamente — ver `src/db/models_registry.py`.
import src.db.models_registry  # noqa: F401
from pydantic import ValidationError
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser
from src.features.issues.exceptions import (
    InvalidParentIssueError,
    IssueHasSubIssuesError,
    IssueLabelAlreadyAppliedError,
    IssueNotFoundError,
    IssueVersionConflictError,
)
from src.features.issues.models import IssuePriority
from src.features.issues.schemas import IssueCreateRequest, IssueUpdateRequest
from src.features.issues.service import IssueService
from src.features.labels.exceptions import LabelNotFoundError
from src.features.labels.models import Label
from src.features.notifications.models import NotificationType
from src.features.notifications.service import NotificationService
from src.features.projects.exceptions import ProjectNotFoundError
from src.features.projects.models import Project
from src.features.workflow_states.exceptions import WorkflowStateNotFoundError
from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole

from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.labels.fakes import FakeLabelRepository
from tests.unit.features.notifications.fakes import FakeNotificationRepository
from tests.unit.features.projects.fakes import FakeProjectRepository
from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository

# Autorização por papel para create/read/update é resolvida pelo router via
# `Depends(require_permission(...))` (mesmo racional de `test_project_service.py`)
# — o que resta testável aqui é regra de negócio pura + a única checagem
# contextual que o service de fato resolve: posse na exclusão (ADR-012, Decisão 6).


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def project_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def label_repo() -> FakeLabelRepository:
    return FakeLabelRepository()


@pytest.fixture
def notification_repo() -> FakeNotificationRepository:
    return FakeNotificationRepository()


@pytest.fixture
def notification_service(notification_repo: FakeNotificationRepository) -> NotificationService:
    return NotificationService(notification_repo)


@pytest.fixture
def workflow_state_repo() -> FakeWorkflowStateRepository:
    return FakeWorkflowStateRepository()


@pytest.fixture
def service(
    issue_repo: FakeIssueRepository,
    project_repo: FakeProjectRepository,
    label_repo: FakeLabelRepository,
    notification_service: NotificationService,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> IssueService:
    return IssueService(
        issue_repo,
        PermissionService(),
        project_repo,
        label_repo,
        notification_service,
        workflow_state_repo,
    )


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


def _workspace_id() -> uuid.UUID:
    return uuid.uuid4()


def _member(workspace_id: uuid.UUID, user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)


async def _seed_status(
    workflow_state_repo: FakeWorkflowStateRepository,
    workspace_id: uuid.UUID,
    *,
    name: str = "Backlog",
    category: WorkflowStateCategory = WorkflowStateCategory.BACKLOG,
    position: int = 0,
    is_default: bool = True,
) -> WorkflowState:
    """Mimetiza `WorkflowStateService.seed_defaults` (chamado por
    `WorkspaceService.create` em produção) — testes unitários usam workspaces
    ad-hoc (`_workspace_id()`), então precisam semear o status default à mão
    antes de criar uma issue sem `status_id` explícito."""
    return await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace_id,
            name=name,
            category=category,
            position=position,
            is_default=is_default,
        )
    )


async def test_create_generates_sequential_number_and_identifier(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    default_status = await _seed_status(workflow_state_repo, workspace_id)
    creator = _user()

    first = await service.create(creator, workspace_id, IssueCreateRequest(title="Bug de login"))
    second = await service.create(creator, workspace_id, IssueCreateRequest(title="Outro bug"))

    assert first.number == 1
    assert first.identifier == "FD-1"
    assert second.number == 2
    assert second.identifier == "FD-2"
    assert first.creator_id == creator.id
    assert first.status_id == default_status.id
    assert any(entry.action == "issue.created" for entry in issue_repo.activity_log)


async def test_create_rejects_project_from_another_workspace(
    service: IssueService,
    project_repo: FakeProjectRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    other_workspace_project = await project_repo.create(
        Project(
            workspace_id=_workspace_id(),
            name="Roadmap",
            slug="roadmap",
            created_by=uuid.uuid4(),
        )
    )

    with pytest.raises(ProjectNotFoundError):
        await service.create(
            _user(),
            workspace_id,
            IssueCreateRequest(title="Issue", project_id=other_workspace_project.id),
        )


async def test_create_rejects_status_from_another_workspace(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    foreign_status = await _seed_status(workflow_state_repo, _workspace_id(), name="Foreign")

    with pytest.raises(WorkflowStateNotFoundError):
        await service.create(
            _user(), workspace_id, IssueCreateRequest(title="Issue", status_id=foreign_status.id)
        )


async def test_get_raises_not_found_for_missing_issue(service: IssueService) -> None:
    with pytest.raises(IssueNotFoundError):
        await service.get(_workspace_id(), uuid.uuid4())


async def test_get_raises_not_found_across_workspaces(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    issue = await service.create(_user(), workspace_id, IssueCreateRequest(title="Issue"))

    with pytest.raises(IssueNotFoundError):
        await service.get(_workspace_id(), issue.id)


async def test_list_for_workspace_filters_by_status_and_priority(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    todo_status = await _seed_status(
        workflow_state_repo,
        workspace_id,
        name="Todo",
        category=WorkflowStateCategory.UNSTARTED,
        position=1,
        is_default=False,
    )
    actor = _user()
    todo = await service.create(
        actor, workspace_id, IssueCreateRequest(title="A fazer", status_id=todo_status.id)
    )
    await service.create(
        actor,
        workspace_id,
        IssueCreateRequest(title="Urgente", priority=IssuePriority.URGENT),
    )

    status_filtered, status_total = await service.list_for_workspace(
        workspace_id,
        page=1,
        per_page=20,
        project_id=None,
        parent_id=None,
        status_id=todo_status.id,
        priority=None,
        assignee_id=None,
        creator_id=None,
        search=None,
        sort="-updated_at",
    )
    priority_filtered, priority_total = await service.list_for_workspace(
        workspace_id,
        page=1,
        per_page=20,
        project_id=None,
        parent_id=None,
        status_id=None,
        priority=IssuePriority.URGENT,
        assignee_id=None,
        creator_id=None,
        search=None,
        sort="-updated_at",
    )

    assert status_total == 1
    assert status_filtered[0].id == todo.id
    assert priority_total == 1
    assert priority_filtered[0].priority == IssuePriority.URGENT


async def test_update_changes_status_and_records_status_changed_activity(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    in_progress = await _seed_status(
        workflow_state_repo,
        workspace_id,
        name="In Progress",
        category=WorkflowStateCategory.STARTED,
        position=1,
        is_default=False,
    )
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))

    updated = await service.update(
        actor, workspace_id, issue.id, IssueUpdateRequest(status_id=in_progress.id)
    )

    assert updated.status_id == in_progress.id
    assert updated.version == 2
    assert any(entry.action == "issue.status_changed" for entry in issue_repo.activity_log)


async def test_update_status_change_notifies_assignee(
    service: IssueService,
    notification_repo: FakeNotificationRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    in_progress = await _seed_status(
        workflow_state_repo,
        workspace_id,
        name="In Progress",
        category=WorkflowStateCategory.STARTED,
        position=1,
        is_default=False,
    )
    actor = _user()
    assignee_id = uuid.uuid4()
    issue = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Issue", assignee_id=assignee_id)
    )

    await service.update(
        actor, workspace_id, issue.id, IssueUpdateRequest(status_id=in_progress.id)
    )

    notifications = list(notification_repo.notifications.values())
    assert len(notifications) == 1
    assert notifications[0].user_id == assignee_id
    assert notifications[0].type == NotificationType.STATUS_CHANGE
    assert notifications[0].payload["issue_identifier"] == issue.identifier
    assert notifications[0].payload["new_status"] == "In Progress"


async def test_update_status_change_does_not_notify_when_unassigned(
    service: IssueService,
    notification_repo: FakeNotificationRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    in_progress = await _seed_status(
        workflow_state_repo,
        workspace_id,
        name="In Progress",
        category=WorkflowStateCategory.STARTED,
        position=1,
        is_default=False,
    )
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))

    await service.update(
        actor, workspace_id, issue.id, IssueUpdateRequest(status_id=in_progress.id)
    )

    assert notification_repo.notifications == {}


async def test_update_status_change_does_not_notify_self_assigned_actor(
    service: IssueService,
    notification_repo: FakeNotificationRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    in_progress = await _seed_status(
        workflow_state_repo,
        workspace_id,
        name="In Progress",
        category=WorkflowStateCategory.STARTED,
        position=1,
        is_default=False,
    )
    actor = _user()
    issue = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Issue", assignee_id=actor.id)
    )

    await service.update(
        actor, workspace_id, issue.id, IssueUpdateRequest(status_id=in_progress.id)
    )

    assert notification_repo.notifications == {}


async def test_update_with_no_changes_does_not_record_activity_or_bump_version(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    issue_repo.activity_log.clear()

    updated = await service.update(actor, workspace_id, issue.id, IssueUpdateRequest(title="Issue"))

    assert updated.version == 1
    assert issue_repo.activity_log == []


async def test_update_raises_version_conflict_on_stale_expected_version(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    await service.update(actor, workspace_id, issue.id, IssueUpdateRequest(title="Renomeada"))

    with pytest.raises(IssueVersionConflictError):
        await service.update(
            actor,
            workspace_id,
            issue.id,
            IssueUpdateRequest(title="Outra mudança"),
            expected_version=1,
        )


async def test_update_validates_new_project_belongs_to_workspace(
    service: IssueService,
    project_repo: FakeProjectRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    foreign_project = await project_repo.create(
        Project(
            workspace_id=_workspace_id(),
            name="Roadmap",
            slug="roadmap",
            created_by=uuid.uuid4(),
        )
    )

    with pytest.raises(ProjectNotFoundError):
        await service.update(
            actor, workspace_id, issue.id, IssueUpdateRequest(project_id=foreign_project.id)
        )


async def test_update_clears_due_date_when_explicitly_set_to_none(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Issue", due_date=date(2026, 1, 1))
    )

    updated = await service.update(actor, workspace_id, issue.id, IssueUpdateRequest(due_date=None))

    assert updated.due_date is None
    assert updated.version == 2
    assert any(
        entry.action == "issue.updated" and entry.field == "due_date"
        for entry in issue_repo.activity_log
    )


async def test_update_omitting_due_date_leaves_it_unchanged(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Issue", due_date=date(2026, 1, 1))
    )
    issue_repo.activity_log.clear()

    updated = await service.update(actor, workspace_id, issue.id, IssueUpdateRequest(title="Issue"))

    assert updated.due_date == date(2026, 1, 1)
    assert updated.version == 1
    assert issue_repo.activity_log == []


@pytest.mark.parametrize("request_cls", [IssueCreateRequest, IssueUpdateRequest])
def test_due_date_outside_business_range_is_rejected(request_cls: type) -> None:
    kwargs = {"title": "Issue"} if request_cls is IssueCreateRequest else {}

    with pytest.raises(ValidationError):
        request_cls(**kwargs, due_date=date(2, 1, 1))


@pytest.mark.parametrize("request_cls", [IssueCreateRequest, IssueUpdateRequest])
def test_due_date_within_business_range_is_accepted(request_cls: type) -> None:
    kwargs = {"title": "Issue"} if request_cls is IssueCreateRequest else {}

    payload = request_cls(**kwargs, due_date=date(2026, 1, 1))

    assert payload.due_date == date(2026, 1, 1)


async def test_delete_by_creator_succeeds_via_ownership_override(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    creator_member = _member(workspace_id, creator.id, WorkspaceRole.MEMBER)

    await service.delete(creator_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is not None
    assert any(entry.action == "issue.deleted" for entry in issue_repo.activity_log)


async def test_delete_by_non_creator_member_raises_permission_denied(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    other_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.MEMBER)

    with pytest.raises(PermissionDeniedError):
        await service.delete(other_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is None


async def test_delete_by_admin_succeeds_without_being_creator(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    admin_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.ADMIN)

    await service.delete(admin_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is not None


async def test_add_label_links_label_and_records_activity(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    label_repo: FakeLabelRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))

    added = await service.add_label(actor, workspace_id, issue.id, label.id)

    assert added.id == label.id
    assert any(link.label_id == label.id for link in issue_repo.labels)
    assert any(entry.action == "label.added" for entry in issue_repo.activity_log)


async def test_add_label_rejects_label_from_another_workspace(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    label_repo: FakeLabelRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    foreign_label = await label_repo.create(
        Label(workspace_id=_workspace_id(), name="bug", color="#FF0000")
    )

    with pytest.raises(LabelNotFoundError):
        await service.add_label(actor, workspace_id, issue.id, foreign_label.id)


async def test_add_label_twice_raises_conflict(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    label_repo: FakeLabelRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))
    await service.add_label(actor, workspace_id, issue.id, label.id)

    with pytest.raises(IssueLabelAlreadyAppliedError):
        await service.add_label(actor, workspace_id, issue.id, label.id)


async def test_remove_label_unlinks_and_records_activity(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    label_repo: FakeLabelRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))
    await service.add_label(actor, workspace_id, issue.id, label.id)
    issue_repo.activity_log.clear()

    await service.remove_label(actor, workspace_id, issue.id, label.id)

    assert not any(link.label_id == label.id for link in issue_repo.labels)
    assert any(entry.action == "label.removed" for entry in issue_repo.activity_log)


async def test_create_with_parent_id_links_sub_issue(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    parent = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico"))

    child = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Sub-tarefa", parent_id=parent.id)
    )

    assert child.parent_id == parent.id


async def test_create_rejects_self_as_parent_is_impossible_but_rejects_unknown_parent(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)

    with pytest.raises(IssueNotFoundError):
        await service.create(
            _user(), workspace_id, IssueCreateRequest(title="Sub-tarefa", parent_id=uuid.uuid4())
        )


async def test_create_rejects_parent_that_is_already_a_sub_issue(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    grandparent = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico"))
    parent = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Filho", parent_id=grandparent.id)
    )

    with pytest.raises(InvalidParentIssueError):
        await service.create(
            actor, workspace_id, IssueCreateRequest(title="Neto", parent_id=parent.id)
        )


async def test_create_rejects_parent_that_already_has_children(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    parent = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico"))
    await service.create(
        actor, workspace_id, IssueCreateRequest(title="Filho 1", parent_id=parent.id)
    )

    with pytest.raises(InvalidParentIssueError):
        await service.create(
            actor, workspace_id, IssueCreateRequest(title="Filho 2", parent_id=parent.id)
        )


async def test_update_links_and_unlinks_parent(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    parent = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico"))
    child = await service.create(actor, workspace_id, IssueCreateRequest(title="Solta"))

    linked = await service.update(
        actor, workspace_id, child.id, IssueUpdateRequest(parent_id=parent.id)
    )
    assert linked.parent_id == parent.id
    assert any(
        entry.field == "parent_id" and entry.new_value == str(parent.id)
        for entry in issue_repo.activity_log
    )

    unlinked = await service.update(
        actor, workspace_id, child.id, IssueUpdateRequest(parent_id=None)
    )
    assert unlinked.parent_id is None


async def test_update_rejects_linking_an_issue_that_already_has_children(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    parent_a = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico A"))
    await service.create(
        actor, workspace_id, IssueCreateRequest(title="Filho de A", parent_id=parent_a.id)
    )
    parent_b = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico B"))

    with pytest.raises(InvalidParentIssueError):
        await service.update(
            actor, workspace_id, parent_a.id, IssueUpdateRequest(parent_id=parent_b.id)
        )


async def test_update_rejects_self_parenting(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    issue = await service.create(_user(), workspace_id, IssueCreateRequest(title="Issue"))

    with pytest.raises(InvalidParentIssueError):
        await service.update(
            _user(), workspace_id, issue.id, IssueUpdateRequest(parent_id=issue.id)
        )


async def test_delete_blocks_when_issue_has_sub_issues(
    service: IssueService,
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    creator = _user()
    parent = await service.create(creator, workspace_id, IssueCreateRequest(title="Épico"))
    await service.create(
        creator, workspace_id, IssueCreateRequest(title="Filho", parent_id=parent.id)
    )
    creator_member = _member(workspace_id, creator.id, WorkspaceRole.MEMBER)

    with pytest.raises(IssueHasSubIssuesError):
        await service.delete(creator_member, workspace_id, parent.id)

    assert issue_repo.issues[parent.id].deleted_at is None


async def test_list_for_workspace_filters_by_parent_id(
    service: IssueService, workflow_state_repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await _seed_status(workflow_state_repo, workspace_id)
    actor = _user()
    parent = await service.create(actor, workspace_id, IssueCreateRequest(title="Épico"))
    child = await service.create(
        actor, workspace_id, IssueCreateRequest(title="Filho", parent_id=parent.id)
    )
    await service.create(actor, workspace_id, IssueCreateRequest(title="Solta"))

    children, total = await service.list_for_workspace(
        workspace_id,
        page=1,
        per_page=20,
        project_id=None,
        parent_id=parent.id,
        status_id=None,
        priority=None,
        assignee_id=None,
        creator_id=None,
        search=None,
        sort="-updated_at",
    )

    assert total == 1
    assert children[0].id == child.id
