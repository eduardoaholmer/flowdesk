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
    ProjectNameTakenError,
    ProjectNotArchivedError,
    ProjectNotFoundError,
    ProjectSlugTakenError,
)
from src.features.projects.models import ProjectStatus
from src.features.projects.schemas import ProjectCreateRequest, ProjectUpdateRequest
from src.features.projects.service import ProjectService

from tests.unit.features.projects.fakes import FakeProjectRepository

# Autorização por papel (quem pode criar/editar/excluir um projeto) não é
# checada por este service — o router resolve `Depends(require_permission(...))`
# antes de chamá-lo (mesmo racional de `test_workspace_service.py`). O que
# resta testável aqui é regra de negócio pura: unicidade de nome/slug por
# workspace, transição de status (archive/restore) e a restrição de exclusão
# quando há issues ativas vinculadas.


@pytest.fixture
def project_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def service(project_repo: FakeProjectRepository) -> ProjectService:
    return ProjectService(project_repo)


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


def _workspace_id() -> uuid.UUID:
    return uuid.uuid4()


async def test_create_generates_slug_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    creator = _user()

    project = await service.create(creator, workspace_id, ProjectCreateRequest(name="Roadmap Q3"))

    assert project.slug.startswith("roadmap-q3")
    assert project.status == ProjectStatus.ACTIVE
    assert project.created_by == creator.id
    assert any(entry.action == "project.created" for entry in project_repo.activity_log)


async def test_create_rejects_duplicate_name_case_insensitive(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNameTakenError):
        await service.create(_user(), workspace_id, ProjectCreateRequest(name="ROADMAP"))


async def test_create_allows_same_name_in_different_workspaces(service: ProjectService) -> None:
    await service.create(_user(), _workspace_id(), ProjectCreateRequest(name="Roadmap"))

    project = await service.create(_user(), _workspace_id(), ProjectCreateRequest(name="Roadmap"))

    assert project.name == "Roadmap"


async def test_create_rejects_taken_slug(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    await service.create(
        _user(), workspace_id, ProjectCreateRequest(name="Roadmap", slug="roadmap")
    )

    with pytest.raises(ProjectSlugTakenError):
        await service.create(
            _user(), workspace_id, ProjectCreateRequest(name="Other", slug="roadmap")
        )


async def test_get_raises_not_found_for_missing_project(service: ProjectService) -> None:
    with pytest.raises(ProjectNotFoundError):
        await service.get(_workspace_id(), uuid.uuid4())


async def test_get_raises_not_found_across_workspaces(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    project = await service.create(_user(), workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNotFoundError):
        await service.get(_workspace_id(), project.id)


async def test_list_for_workspace_filters_by_search_and_status(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    active = await service.create(actor, workspace_id, ProjectCreateRequest(name="Onboarding"))
    archived = await service.create(actor, workspace_id, ProjectCreateRequest(name="Legacy Import"))
    await service.archive(actor, workspace_id, archived.id)

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
    assert active_only[0].id == active.id
    assert searched_total == 1
    assert searched[0].id == archived.id


async def test_update_renames_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    updated = await service.update(
        actor, workspace_id, project.id, ProjectUpdateRequest(name="Roadmap 2026")
    )

    assert updated.name == "Roadmap 2026"
    assert any(entry.action == "project.updated" for entry in project_repo.activity_log)


async def test_update_rejects_duplicate_name(service: ProjectService) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    other = await service.create(actor, workspace_id, ProjectCreateRequest(name="Backlog"))

    with pytest.raises(ProjectNameTakenError):
        await service.update(actor, workspace_id, other.id, ProjectUpdateRequest(name="roadmap"))


async def test_update_with_no_changes_does_not_record_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    project_repo.activity_log.clear()

    await service.update(actor, workspace_id, project.id, ProjectUpdateRequest(name="Roadmap"))

    assert project_repo.activity_log == []


async def test_archive_transitions_status_and_rejects_double_archive(
    service: ProjectService,
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    archived = await service.archive(actor, workspace_id, project.id)
    assert archived.status == ProjectStatus.ARCHIVED

    with pytest.raises(ProjectAlreadyArchivedError):
        await service.archive(actor, workspace_id, project.id)


async def test_restore_transitions_status_and_rejects_when_not_archived(
    service: ProjectService,
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    with pytest.raises(ProjectNotArchivedError):
        await service.restore(actor, workspace_id, project.id)

    await service.archive(actor, workspace_id, project.id)
    restored = await service.restore(actor, workspace_id, project.id)
    assert restored.status == ProjectStatus.ACTIVE


async def test_delete_soft_deletes_and_records_activity(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))

    await service.delete(actor, workspace_id, project.id)

    assert project_repo.projects[project.id].deleted_at is not None
    with pytest.raises(ProjectNotFoundError):
        await service.get(workspace_id, project.id)
    assert any(entry.action == "project.deleted" for entry in project_repo.activity_log)


async def test_delete_blocked_when_project_has_active_issues(
    service: ProjectService, project_repo: FakeProjectRepository
) -> None:
    workspace_id = _workspace_id()
    actor = _user()
    project = await service.create(actor, workspace_id, ProjectCreateRequest(name="Roadmap"))
    project_repo.projects_with_active_issues.add(project.id)

    with pytest.raises(ProjectHasActiveIssuesError):
        await service.delete(actor, workspace_id, project.id)

    assert project_repo.projects[project.id].deleted_at is None
