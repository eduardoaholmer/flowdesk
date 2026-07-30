import uuid

import pytest
from src.core.exceptions import ValidationError
from src.features.workflow_states.exceptions import (
    CannotDeleteLastWorkflowStateError,
    InvalidReassignTargetError,
    WorkflowStateHasIssuesError,
    WorkflowStateNameTakenError,
    WorkflowStateNotFoundError,
)
from src.features.workflow_states.schemas import (
    WorkflowStateCreateRequest,
    WorkflowStateReorderRequest,
    WorkflowStateUpdateRequest,
)
from src.features.workflow_states.service import WorkflowStateService

from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository


@pytest.fixture
def repo() -> FakeWorkflowStateRepository:
    return FakeWorkflowStateRepository()


@pytest.fixture
def service(repo: FakeWorkflowStateRepository) -> WorkflowStateService:
    return WorkflowStateService(repo)


def _workspace_id() -> uuid.UUID:
    return uuid.uuid4()


async def test_seed_defaults_creates_six_states_with_one_default(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()

    await service.seed_defaults(workspace_id)

    states = await repo.list_by_workspace(workspace_id)
    assert len(states) == 6
    assert [s.position for s in states] == [0, 1, 2, 3, 4, 5]
    assert sum(1 for s in states if s.is_default) == 1
    assert states[0].name == "Backlog"
    assert states[0].is_default is True


async def test_create_rejects_duplicate_name(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    await service.create(workspace_id, WorkflowStateCreateRequest(name="Doing", category="STARTED"))

    with pytest.raises(WorkflowStateNameTakenError):
        await service.create(
            workspace_id, WorkflowStateCreateRequest(name="Doing", category="STARTED")
        )


async def test_create_appends_after_max_position(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)

    created = await service.create(
        workspace_id, WorkflowStateCreateRequest(name="Blocked", category="STARTED")
    )

    assert created.workflow_state.position == 6


async def test_create_with_is_default_clears_previous_default(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)

    created = await service.create(
        workspace_id,
        WorkflowStateCreateRequest(name="Triage", category="BACKLOG", is_default=True),
    )

    old_default = await repo.get_by_name(workspace_id, "Backlog")
    assert old_default is not None
    assert old_default.is_default is False
    assert created.workflow_state.is_default is True


async def test_update_renames_state(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    created = await service.create(
        workspace_id, WorkflowStateCreateRequest(name="Doing", category="STARTED")
    )

    updated = await service.update(
        workspace_id, created.workflow_state.id, WorkflowStateUpdateRequest(name="In Progress")
    )

    assert updated.workflow_state.name == "In Progress"


async def test_update_rejects_rename_to_existing_name(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    await service.create(workspace_id, WorkflowStateCreateRequest(name="Doing", category="STARTED"))
    other = await service.create(
        workspace_id, WorkflowStateCreateRequest(name="Blocked", category="STARTED")
    )

    with pytest.raises(WorkflowStateNameTakenError):
        await service.update(
            workspace_id, other.workflow_state.id, WorkflowStateUpdateRequest(name="Doing")
        )


async def test_update_not_found_raises(service: WorkflowStateService) -> None:
    with pytest.raises(WorkflowStateNotFoundError):
        await service.update(_workspace_id(), uuid.uuid4(), WorkflowStateUpdateRequest(name="x"))


async def test_reorder_applies_new_positions(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    ids = [s.workflow_state.id for s in states]
    # Inverte a ordem inteira — troca direta de posições entre linhas.
    reversed_ids = list(reversed(ids))

    reordered = await service.reorder(
        workspace_id, WorkflowStateReorderRequest(ordered_ids=reversed_ids)
    )

    assert [s.workflow_state.id for s in reordered] == reversed_ids
    assert [s.workflow_state.position for s in reordered] == [0, 1, 2, 3, 4, 5]


async def test_reorder_rejects_incomplete_list(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    partial_ids = [states[0].workflow_state.id]

    with pytest.raises(ValidationError):
        await service.reorder(workspace_id, WorkflowStateReorderRequest(ordered_ids=partial_ids))


async def test_delete_blocks_last_remaining_state(service: WorkflowStateService) -> None:
    workspace_id = _workspace_id()
    only = await service.create(
        workspace_id, WorkflowStateCreateRequest(name="Only", category="BACKLOG")
    )

    with pytest.raises(CannotDeleteLastWorkflowStateError):
        await service.delete(workspace_id, only.workflow_state.id, None)


async def test_delete_without_issues_succeeds(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    target = next(s for s in states if s.workflow_state.name == "Canceled")

    await service.delete(workspace_id, target.workflow_state.id, None)

    remaining = await repo.list_by_workspace(workspace_id)
    assert target.workflow_state.id not in [s.id for s in remaining]


async def test_delete_with_issues_requires_reassign_target(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    target = next(s for s in states if s.workflow_state.name == "Todo")
    repo.issue_count_by_state[target.workflow_state.id] = 3

    with pytest.raises(WorkflowStateHasIssuesError) as exc_info:
        await service.delete(workspace_id, target.workflow_state.id, None)
    assert exc_info.value.details == {"issue_count": 3}


async def test_delete_with_issues_reassigns_when_target_given(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    source = next(s for s in states if s.workflow_state.name == "Todo")
    destination = next(s for s in states if s.workflow_state.name == "Backlog")
    repo.issue_count_by_state[source.workflow_state.id] = 3

    await service.delete(workspace_id, source.workflow_state.id, destination.workflow_state.id)

    assert repo.reassignments == [(source.workflow_state.id, destination.workflow_state.id)]
    assert repo.issue_count_by_state[destination.workflow_state.id] == 3


async def test_delete_rejects_invalid_reassign_target(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    target = next(s for s in states if s.workflow_state.name == "Todo")
    repo.issue_count_by_state[target.workflow_state.id] = 1

    with pytest.raises(InvalidReassignTargetError):
        await service.delete(workspace_id, target.workflow_state.id, uuid.uuid4())


async def test_delete_promotes_new_default_when_default_removed(
    service: WorkflowStateService, repo: FakeWorkflowStateRepository
) -> None:
    workspace_id = _workspace_id()
    await service.seed_defaults(workspace_id)
    states = await service.list_for_workspace(workspace_id)
    default_state = next(s for s in states if s.workflow_state.is_default)

    await service.delete(workspace_id, default_state.workflow_state.id, None)

    remaining = await repo.list_by_workspace(workspace_id)
    assert sum(1 for s in remaining if s.is_default) == 1
