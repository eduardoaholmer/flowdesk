import uuid

import pytest

# Garante que os relacionamentos entre features (`Project.issues` -> `Issue`,
# `Issue.comments` -> `Comment`) estejam resolvíveis antes de instanciar
# `Project` isoladamente — ver `src/db/models_registry.py`.
import src.db.models_registry  # noqa: F401
from src.core.security import CurrentUser
from src.features.projects.exceptions import (
    ProjectAlreadyArchivedError,
    ProjectHasActiveIssuesError,
    ProjectKeyTakenError,
    ProjectMemberNotInWorkspaceError,
    ProjectNameTakenError,
    ProjectNotArchivedError,
    ProjectNotFoundError,
    ProjectSlugTakenError,
)
from src.features.projects.models import ProjectStatus
from src.features.projects.schemas import ProjectCreateRequest, ProjectUpdateRequest
from src.features.projects.service import ProjectService
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole

from tests.unit.features.projects.fakes import FakeProjectRepository
from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository

# Autorização por papel (quem pode criar/editar/excluir um projeto) não é
# checada por este service — o router resolve `Depends(require_permission(...))`
# antes de chamá-lo (mesmo racional de `test_workspace_service.py`). O que
# resta testável aqui é regra de negócio pura: unicidade de nome/slug/key por
# workspace, transição de status (archive/restore), a restrição de exclusão
# quando há issues ativas, membership informativa e os agregados de progresso.


@pytest.fixture
def project_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def workspace_repo() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def service(
    project_repo: FakeProjectRepository, workspace_repo: FakeWorkspaceRepository
) -> ProjectService:
    return ProjectService(project_repo, workspace_repo)


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


def _workspace_id() -> uuid.UUID:
    return uuid.uuid4()


def _add_workspace_member(
    workspace_repo: FakeWorkspaceRepository, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    workspace_repo.members[uuid.uuid4()] = WorkspaceMember(
        workspace_id=workspace_id, user_id=user_id, role=WorkspaceRole.MEMBER
    )


async def test_create_generates_slug_key_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()

    view = await service.create(creator, workspace_id, ProjectCreateRequest(name="Roadmap Q3"))

    assert view.project.slug.startswith("roadmap-q3")
    assert view.project.key == "RQ"
    assert view.project.status == ProjectStatus.ACTIVE
    assert view.project.created_by == creator.id
    assert view.member_ids == []
    assert view.issue_count == 0
    assert view.done_issue_count == 0
    assert any(entry.action == "project.created" for entry in project_repo.activity_log)


async def test_create_derives_key_from_single_word_name(service: ProjectService) -> None:
    view = await service.create(_user(), _workspace_id(), ProjectCreateRequest(name="Palette"))

    assert view.project.key == "PAL"


async def test_create_rejects_duplicate_name_case_insensitive(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNameTakenError):
        await service.create(_user(), workspace_id, ProjectCreateRequest(name="ROADMAP"))


async def test_create_allows_same_name_in_different_workspaces(service: ProjectService) -> None:
    await service.create(_user(), _workspace_id(), ProjectCreateRequest(name="Roadmap"))

    view = await service.create(_user(), _workspace_id(), ProjectCreateRequest(name="Roadmap"))

    assert view.project.name == "Roadmap"


async def test_create_rejects_taken_slug(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    await service.create(
        _user(), workspace_id, ProjectCreateRequest(name="Roadmap", slug="roadmap")
    )

    with pytest.raises(ProjectSlugTakenError):
        await service.create(
            _user(), workspace_id, ProjectCreateRequest(name="Other", slug="roadmap")
        )


async def test_create_rejects_taken_key(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap", key="RMP"))

    with pytest.raises(ProjectKeyTakenError):
        await service.create(_user(), workspace_id, ProjectCreateRequest(name="Other", key="RMP"))


async def test_create_auto_key_avoids_collision(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    first = await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap Quest"))
    second = await service.create(_user(), workspace_id, ProjectCreateRequest(name="Rapid Quality"))

    assert first.project.key == "RQ"
    assert second.project.key != first.project.key


async def test_get_raises_not_found_for_missing_project(service: ProjectService) -> None:
    with pytest.raises(ProjectNotFoundError):
        await service.get(_workspace_id(), uuid.uuid4())


async def test_get_raises_not_found_across_workspaces(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    created = await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNotFoundError):
        await service.get(_workspace_id(), created.project.id)


async def test_get_exposes_member_ids_and_issue_progress(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    project_repo.issue_count_by_project[created.project.id] = (5, 2)

    view = await service.get(workspace_id, created.project.id)

    assert view.issue_count == 5
    assert view.done_issue_count == 2


async def test_list_for_workspace_filters_by_search_and_status(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    active = await service.create(actor, workspace_id, ProjectCreateRequest(name="Onboarding"))
    archived = await service.create(actor, workspace_id, ProjectCreateRequest(name="Legacy Import"))
    await service.archive(actor, workspace_id, archived.project.id)

    active_only, active_total = await service.list_for_workspace(
        workspace_id,
        page=1,
        per_page=20,
        search=None,
        status=ProjectStatus.ACTIVE,
        sort="-created_at",
    )
    searched, searched_total = await service.list_for_workspace(
        workspace_id, page=1, per_page=20, search="legacy", status=None, sort="-created_at"
    )

    assert active_total == 1
    assert active_only[0].project.id == active.project.id
    assert searched_total == 1
    assert searched[0].project.id == archived.project.id


async def test_update_renames_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    updated = await service.update(
        actor, workspace_id, created.project.id, ProjectUpdateRequest(name="Roadmap 2026")
    )

    assert updated.project.name == "Roadmap 2026"
    assert any(entry.action == "project.updated" for entry in project_repo.activity_log)


async def test_update_changes_key_and_rejects_duplicate(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap", key="RMP"))
    other = await service.create(
        actor, workspace_id, ProjectCreateRequest(name="Backlog", key="BKL")
    )

    changed = await service.update(
        actor, workspace_id, other.project.id, ProjectUpdateRequest(key="bck")
    )
    assert changed.project.key == "BCK"

    with pytest.raises(ProjectKeyTakenError):
        await service.update(actor, workspace_id, other.project.id, ProjectUpdateRequest(key="RMP"))


async def test_update_rejects_duplicate_name(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    other = await service.create(actor, workspace_id, ProjectCreateRequest(name="Backlog"))

    with pytest.raises(ProjectNameTakenError):
        await service.update(
            actor, workspace_id, other.project.id, ProjectUpdateRequest(name="roadmap")
        )


async def test_update_with_no_changes_does_not_record_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    project_repo.activity_log.clear()

    await service.update(
        actor, workspace_id, created.project.id, ProjectUpdateRequest(name="Roadmap")
    )

    assert project_repo.activity_log == []


async def test_archive_transitions_status_and_rejects_double_archive(
    service: ProjectService,
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    archived = await service.archive(actor, workspace_id, created.project.id)
    assert archived.project.status == ProjectStatus.ARCHIVED

    with pytest.raises(ProjectAlreadyArchivedError):
        await service.archive(actor, workspace_id, created.project.id)


async def test_restore_transitions_status_and_rejects_when_not_archived(
    service: ProjectService,
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNotArchivedError):
        await service.restore(actor, workspace_id, created.project.id)

    await service.archive(actor, workspace_id, created.project.id)
    restored = await service.restore(actor, workspace_id, created.project.id)
    assert restored.project.status == ProjectStatus.ACTIVE


async def test_add_member_is_idempotent_and_lists_member_ids(
    service: ProjectService,
    project_repo: FakeProjectRepository,
    workspace_repo: FakeWorkspaceRepository,
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    member = _user("grace@example.com")
    _add_workspace_member(workspace_repo, workspace_id, member.id)
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    first = await service.add_member(actor, workspace_id, created.project.id, member.id)
    second = await service.add_member(actor, workspace_id, created.project.id, member.id)

    assert first.member_ids == [member.id]
    assert second.member_ids == [member.id]
    assert sum(1 for e in project_repo.activity_log if e.action == "project.member_added") == 1


async def test_add_member_rejects_non_workspace_member(
    service: ProjectService, workspace_repo: FakeWorkspaceRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectMemberNotInWorkspaceError):
        await service.add_member(actor, workspace_id, created.project.id, uuid.uuid4())


async def test_remove_member_drops_from_list(
    service: ProjectService, workspace_repo: FakeWorkspaceRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    member = _user("grace@example.com")
    _add_workspace_member(workspace_repo, workspace_id, member.id)
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    await service.add_member(actor, workspace_id, created.project.id, member.id)

    view = await service.remove_member(actor, workspace_id, created.project.id, member.id)

    assert view.member_ids == []


async def test_remove_member_on_missing_project_raises(service: ProjectService) -> None:
    with pytest.raises(ProjectNotFoundError):
        await service.remove_member(_user(), _workspace_id(), uuid.uuid4(), uuid.uuid4())


async def test_delete_soft_deletes_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    await service.delete(actor, workspace_id, created.project.id)

    assert project_repo.projects[created.project.id].deleted_at is not None
    with pytest.raises(ProjectNotFoundError):
        await service.get(workspace_id, created.project.id)
    assert any(entry.action == "project.deleted" for entry in project_repo.activity_log)


async def test_delete_blocked_when_project_has_active_issues(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    created = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    project_repo.projects_with_active_issues.add(created.project.id)

    with pytest.raises(ProjectHasActiveIssuesError):
        await service.delete(actor, workspace_id, created.project.id)

    assert project_repo.projects[created.project.id].deleted_at is None
