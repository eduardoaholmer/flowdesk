import uuid

import pytest
from src.core.security import CurrentUser
from src.features.labels.exceptions import LabelNameTakenError, LabelNotFoundError
from src.features.labels.schemas import LabelCreateRequest, LabelUpdateRequest
from src.features.labels.service import LabelService

from tests.unit.features.labels.fakes import FakeLabelRepository


def _user() -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email="ada@example.com", name="Ada Lovelace")


@pytest.fixture
def label_repo() -> FakeLabelRepository:
    return FakeLabelRepository()


@pytest.fixture
def service(label_repo: FakeLabelRepository) -> LabelService:
    return LabelService(label_repo)


async def test_create_records_activity(
    service: LabelService, label_repo: FakeLabelRepository
) -> None:
    workspace_id = uuid.uuid4()

    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )

    assert view.label.name == "bug"
    assert view.label.color == "#FF0000"
    assert view.issue_count == 0
    assert any(entry.action == "label.created" for entry in label_repo.activity_log)


async def test_create_rejects_duplicate_name_in_same_workspace(service: LabelService) -> None:
    workspace_id = uuid.uuid4()
    await service.create(_user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000"))

    with pytest.raises(LabelNameTakenError):
        await service.create(_user(), workspace_id, LabelCreateRequest(name="bug", color="#00FF00"))


async def test_create_allows_same_name_in_different_workspaces(service: LabelService) -> None:
    label_a = await service.create(
        _user(), uuid.uuid4(), LabelCreateRequest(name="bug", color="#FF0000")
    )
    label_b = await service.create(
        _user(), uuid.uuid4(), LabelCreateRequest(name="bug", color="#FF0000")
    )

    assert label_a.label.id != label_b.label.id


async def test_get_raises_not_found_across_workspaces(service: LabelService) -> None:
    workspace_id = uuid.uuid4()
    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )

    with pytest.raises(LabelNotFoundError):
        await service.get(uuid.uuid4(), view.label.id)


async def test_get_exposes_issue_count(
    service: LabelService, label_repo: FakeLabelRepository
) -> None:
    workspace_id = uuid.uuid4()
    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )
    label_repo.issue_count_by_label[view.label.id] = 7

    fetched = await service.get(workspace_id, view.label.id)

    assert fetched.issue_count == 7


async def test_update_renames_and_records_activity(
    service: LabelService, label_repo: FakeLabelRepository
) -> None:
    workspace_id = uuid.uuid4()
    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )
    label_repo.activity_log.clear()

    updated = await service.update(
        _user(), workspace_id, view.label.id, LabelUpdateRequest(name="defeito")
    )

    assert updated.label.name == "defeito"
    assert any(entry.action == "label.updated" for entry in label_repo.activity_log)


async def test_update_rejects_rename_to_taken_name(service: LabelService) -> None:
    workspace_id = uuid.uuid4()
    await service.create(_user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000"))
    feature = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="feature", color="#00FF00")
    )

    with pytest.raises(LabelNameTakenError):
        await service.update(
            _user(), workspace_id, feature.label.id, LabelUpdateRequest(name="bug")
        )


async def test_update_with_no_changes_does_not_record_activity(
    service: LabelService, label_repo: FakeLabelRepository
) -> None:
    workspace_id = uuid.uuid4()
    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )
    label_repo.activity_log.clear()

    await service.update(_user(), workspace_id, view.label.id, LabelUpdateRequest(name="bug"))

    assert label_repo.activity_log == []


async def test_delete_soft_deletes_and_frees_name_for_reuse(
    service: LabelService, label_repo: FakeLabelRepository
) -> None:
    workspace_id = uuid.uuid4()
    view = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )

    await service.delete(_user(), workspace_id, view.label.id)

    assert label_repo.labels[view.label.id].deleted_at is not None
    assert any(entry.action == "label.deleted" for entry in label_repo.activity_log)
    recreated = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#0000FF")
    )
    assert recreated.label.id != view.label.id


async def test_list_for_workspace_excludes_deleted(service: LabelService) -> None:
    workspace_id = uuid.uuid4()
    keep = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="bug", color="#FF0000")
    )
    gone = await service.create(
        _user(), workspace_id, LabelCreateRequest(name="feature", color="#00FF00")
    )
    await service.delete(_user(), workspace_id, gone.label.id)

    views = await service.list_for_workspace(workspace_id)

    assert [view.label.id for view in views] == [keep.label.id]
