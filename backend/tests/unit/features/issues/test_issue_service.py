import uuid

import pytest

# Garante que os relacionamentos entre features (`Project.issues` -> `Issue`,
# `Issue.comments` -> `Comment`) estejam resolvíveis antes de instanciar
# models isoladamente — ver `src/db/models_registry.py`.
import src.db.models_registry  # noqa: F401
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser
from src.features.issues.exceptions import (
    IssueLabelAlreadyAppliedError,
    IssueNotFoundError,
    IssueVersionConflictError,
)
from src.features.issues.models import IssuePriority, IssueStatus
from src.features.issues.schemas import IssueCreateRequest, IssueUpdateRequest
from src.features.issues.service import IssueService
from src.features.labels.exceptions import LabelNotFoundError
from src.features.labels.models import Label
from src.features.projects.exceptions import ProjectNotFoundError
from src.features.projects.models import Project
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole

from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.labels.fakes import FakeLabelRepository
from tests.unit.features.projects.fakes import FakeProjectRepository

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
def service(
    issue_repo: FakeIssueRepository,
    project_repo: FakeProjectRepository,
    label_repo: FakeLabelRepository,
) -> IssueService:
    return IssueService(issue_repo, PermissionService(), project_repo, label_repo)


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


def _workspace_id() -> uuid.UUID:
    return uuid.uuid4()


def _member(workspace_id: uuid.UUID, user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)


async def test_create_generates_sequential_number_and_identifier(
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()

    first = await service.create(creator, workspace_id, IssueCreateRequest(title="Bug de login"))
    second = await service.create(creator, workspace_id, IssueCreateRequest(title="Outro bug"))

    assert first.number == 1
    assert first.identifier == "FD-1"
    assert second.number == 2
    assert second.identifier == "FD-2"
    assert first.creator_id == creator.id
    assert first.status == IssueStatus.BACKLOG
    assert any(entry.action == "issue.created" for entry in issue_repo.activity_log)


async def test_create_rejects_project_from_another_workspace(
    service: IssueService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
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


async def test_get_raises_not_found_for_missing_issue(service: IssueService) -> None:
    with pytest.raises(IssueNotFoundError):
        await service.get(_workspace_id(), uuid.uuid4())


async def test_get_raises_not_found_across_workspaces(service: IssueService) -> None:
    workspace_id = _workspace_id()
    issue = await service.create(_user(), workspace_id, IssueCreateRequest(title="Issue"))

    with pytest.raises(IssueNotFoundError):
        await service.get(_workspace_id(), issue.id)


async def test_list_for_workspace_filters_by_status_and_priority(service: IssueService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    todo = await service.create(
        actor, workspace_id, IssueCreateRequest(title="A fazer", status=IssueStatus.TODO)
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
        status=IssueStatus.TODO,
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
        status=None,
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
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))

    updated = await service.update(
        actor, workspace_id, issue.id, IssueUpdateRequest(status=IssueStatus.IN_PROGRESS)
    )

    assert updated.status == IssueStatus.IN_PROGRESS
    assert updated.version == 2
    assert any(entry.action == "issue.status_changed" for entry in issue_repo.activity_log)


async def test_update_with_no_changes_does_not_record_activity_or_bump_version(
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    issue_repo.activity_log.clear()

    updated = await service.update(actor, workspace_id, issue.id, IssueUpdateRequest(title="Issue"))

    assert updated.version == 1
    assert issue_repo.activity_log == []


async def test_update_raises_version_conflict_on_stale_expected_version(
    service: IssueService,
) -> None:
    workspace_id = _workspace_id()
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
    service: IssueService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
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


async def test_delete_by_creator_succeeds_via_ownership_override(
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    creator_member = _member(workspace_id, creator.id, WorkspaceRole.MEMBER)

    await service.delete(creator_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is not None
    assert any(entry.action == "issue.deleted" for entry in issue_repo.activity_log)


async def test_delete_by_non_creator_member_raises_permission_denied(
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    other_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.MEMBER)

    with pytest.raises(PermissionDeniedError):
        await service.delete(other_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is None


async def test_delete_by_admin_succeeds_without_being_creator(
    service: IssueService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()
    issue = await service.create(creator, workspace_id, IssueCreateRequest(title="Issue"))
    admin_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.ADMIN)

    await service.delete(admin_member, workspace_id, issue.id)

    assert issue_repo.issues[issue.id].deleted_at is not None


async def test_add_label_links_label_and_records_activity(
    service: IssueService, issue_repo: FakeIssueRepository, label_repo: FakeLabelRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))

    added = await service.add_label(actor, workspace_id, issue.id, label.id)

    assert added.id == label.id
    assert any(link.label_id == label.id for link in issue_repo.labels)
    assert any(entry.action == "label.added" for entry in issue_repo.activity_log)


async def test_add_label_rejects_label_from_another_workspace(
    service: IssueService, issue_repo: FakeIssueRepository, label_repo: FakeLabelRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    foreign_label = await label_repo.create(
        Label(workspace_id=_workspace_id(), name="bug", color="#FF0000")
    )

    with pytest.raises(LabelNotFoundError):
        await service.add_label(actor, workspace_id, issue.id, foreign_label.id)


async def test_add_label_twice_raises_conflict(
    service: IssueService, issue_repo: FakeIssueRepository, label_repo: FakeLabelRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))
    await service.add_label(actor, workspace_id, issue.id, label.id)

    with pytest.raises(IssueLabelAlreadyAppliedError):
        await service.add_label(actor, workspace_id, issue.id, label.id)


async def test_remove_label_unlinks_and_records_activity(
    service: IssueService, issue_repo: FakeIssueRepository, label_repo: FakeLabelRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    issue = await service.create(actor, workspace_id, IssueCreateRequest(title="Issue"))
    label = await label_repo.create(Label(workspace_id=workspace_id, name="bug", color="#FF0000"))
    await service.add_label(actor, workspace_id, issue.id, label.id)
    issue_repo.activity_log.clear()

    await service.remove_label(actor, workspace_id, issue.id, label.id)

    assert not any(link.label_id == label.id for link in issue_repo.labels)
    assert any(entry.action == "label.removed" for entry in issue_repo.activity_log)
