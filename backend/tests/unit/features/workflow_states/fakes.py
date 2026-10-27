import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.workflow_states.models import WorkflowState
from uuid6 import uuid7


class FakeWorkflowStateRepository:
    """Implementa `WorkflowStateRepositoryProtocol` em memória (`CLAUDE.md` §5/§6)
    — mesmo racional de `tests/unit/features/labels/fakes.py`."""

    def __init__(self) -> None:
        self.states: dict[uuid.UUID, WorkflowState] = {}
        self.issue_count_by_state: dict[uuid.UUID, int] = {}
        # Controlado pelo teste para simular issues reatribuídas — não há
        # `Issue` real neste fake, só o efeito observável (a contagem some do
        # status de origem e aparece no de destino).
        self.reassignments: list[tuple[uuid.UUID, uuid.UUID]] = []

    async def create(self, state: WorkflowState) -> WorkflowState:
        if state.id is None:
            state.id = uuid7()
        now = datetime.now(UTC)
        state.created_at = state.created_at or now
        state.updated_at = state.updated_at or now
        self.states[state.id] = state
        return state

    async def get_by_id(self, workspace_id: uuid.UUID, state_id: uuid.UUID) -> WorkflowState | None:
        state = self.states.get(state_id)
        if state is None or state.workspace_id != workspace_id or state.deleted_at is not None:
            return None
        return state

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> WorkflowState | None:
        for state in self.states.values():
            if (
                state.workspace_id == workspace_id
                and state.name == name
                and state.deleted_at is None
            ):
                return state
        return None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[WorkflowState]:
        matches = [
            state
            for state in self.states.values()
            if state.workspace_id == workspace_id and state.deleted_at is None
        ]
        matches.sort(key=lambda state: state.position)
        return matches

    async def get_default(self, workspace_id: uuid.UUID) -> WorkflowState | None:
        for state in self.states.values():
            if state.workspace_id == workspace_id and state.is_default and state.deleted_at is None:
                return state
        return None

    async def max_position(self, workspace_id: uuid.UUID) -> int | None:
        positions = [
            state.position
            for state in self.states.values()
            if state.workspace_id == workspace_id and state.deleted_at is None
        ]
        return max(positions) if positions else None

    async def issue_counts(self, state_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
        return {state_id: self.issue_count_by_state.get(state_id, 0) for state_id in state_ids}

    async def reassign_issues(self, from_status_id: uuid.UUID, to_status_id: uuid.UUID) -> None:
        count = self.issue_count_by_state.get(from_status_id, 0)
        self.issue_count_by_state[from_status_id] = 0
        self.issue_count_by_state[to_status_id] = (
            self.issue_count_by_state.get(to_status_id, 0) + count
        )
        self.reassignments.append((from_status_id, to_status_id))

    async def update(self, state: WorkflowState) -> WorkflowState:
        state.updated_at = datetime.now(UTC)
        return state

    async def soft_delete(self, state_id: uuid.UUID) -> None:
        state = self.states.get(state_id)
        if state is not None:
            state.deleted_at = datetime.now(UTC)
