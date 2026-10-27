import uuid

from src.core.exceptions import ValidationError
from src.features.workflow_states.exceptions import (
    CannotDeleteLastWorkflowStateError,
    InvalidReassignTargetError,
    WorkflowStateHasIssuesError,
    WorkflowStateNameTakenError,
    WorkflowStateNotFoundError,
)
from src.features.workflow_states.models import WorkflowState
from src.features.workflow_states.repository import WorkflowStateRepositoryProtocol
from src.features.workflow_states.schemas import (
    WorkflowStateCreateRequest,
    WorkflowStateReorderRequest,
    WorkflowStateUpdateRequest,
    WorkflowStateView,
)

_DEFAULT_SEED: tuple[tuple[str, str, bool], ...] = (
    ("Backlog", "BACKLOG", True),
    ("Todo", "UNSTARTED", False),
    ("In Progress", "STARTED", False),
    ("In Review", "STARTED", False),
    ("Done", "COMPLETED", False),
    ("Canceled", "CANCELED", False),
)


class WorkflowStateService:
    def __init__(self, workflow_state_repo: WorkflowStateRepositoryProtocol) -> None:
        self._repo = workflow_state_repo

    async def seed_defaults(self, workspace_id: uuid.UUID) -> None:
        """Chamado por `WorkspaceService.create` — todo workspace novo nasce com
        os mesmos 6 status que eram o enum fixo antes da Sprint 9.2, para que a
        experiência inicial não mude (ver ADR-056). Editáveis a partir daqui."""
        for position, (name, category, is_default) in enumerate(_DEFAULT_SEED):
            await self._repo.create(
                WorkflowState(
                    workspace_id=workspace_id,
                    name=name,
                    category=category,
                    position=position,
                    is_default=is_default,
                )
            )

    async def create(
        self, workspace_id: uuid.UUID, payload: WorkflowStateCreateRequest
    ) -> WorkflowStateView:
        if await self._repo.get_by_name(workspace_id, payload.name) is not None:
            raise WorkflowStateNameTakenError()

        max_position = await self._repo.max_position(workspace_id)
        position = 0 if max_position is None else max_position + 1

        if payload.is_default:
            await self._clear_current_default(workspace_id)

        state = await self._repo.create(
            WorkflowState(
                workspace_id=workspace_id,
                name=payload.name,
                category=payload.category,
                position=position,
                is_default=payload.is_default,
            )
        )
        return WorkflowStateView(workflow_state=state, issue_count=0)

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> list[WorkflowStateView]:
        states = await self._repo.list_by_workspace(workspace_id)
        counts = await self._repo.issue_counts([state.id for state in states])
        return [
            WorkflowStateView(workflow_state=state, issue_count=counts.get(state.id, 0))
            for state in states
        ]

    async def update(
        self,
        workspace_id: uuid.UUID,
        state_id: uuid.UUID,
        payload: WorkflowStateUpdateRequest,
    ) -> WorkflowStateView:
        state = await self._get_active_state(workspace_id, state_id)

        if payload.name is not None and payload.name != state.name:
            existing = await self._repo.get_by_name(workspace_id, payload.name)
            if existing is not None and existing.id != state.id:
                raise WorkflowStateNameTakenError()
            state.name = payload.name

        if payload.category is not None:
            state.category = payload.category

        if payload.is_default is True and not state.is_default:
            await self._clear_current_default(workspace_id)
            state.is_default = True

        await self._repo.update(state)
        counts = await self._repo.issue_counts([state.id])
        return WorkflowStateView(workflow_state=state, issue_count=counts.get(state.id, 0))

    async def reorder(
        self, workspace_id: uuid.UUID, payload: WorkflowStateReorderRequest
    ) -> list[WorkflowStateView]:
        states = await self._repo.list_by_workspace(workspace_id)
        current_ids = {state.id for state in states}
        if set(payload.ordered_ids) != current_ids or len(payload.ordered_ids) != len(states):
            raise ValidationError(
                "A lista deve conter exatamente os status ativos do workspace, sem repetição."
            )

        # Fase 1: move todas as posições para valores negativos temporários antes
        # de aplicar a ordem final — o índice único parcial `(workspace_id,
        # position)` não é `DEFERRABLE` (Postgres não suporta unique parcial
        # deferrável), então uma troca direta de posições entre duas linhas
        # violaria a constraint no meio do flush, antes do commit.
        states_by_id = {state.id: state for state in states}
        for offset, state in enumerate(states, start=1):
            state.position = -offset
            await self._repo.update(state)

        for position, state_id in enumerate(payload.ordered_ids):
            states_by_id[state_id].position = position
            await self._repo.update(states_by_id[state_id])

        return await self.list_for_workspace(workspace_id)

    async def delete(
        self,
        workspace_id: uuid.UUID,
        state_id: uuid.UUID,
        reassign_to_id: uuid.UUID | None,
    ) -> None:
        state = await self._get_active_state(workspace_id, state_id)

        remaining = await self._repo.list_by_workspace(workspace_id)
        if len(remaining) <= 1:
            raise CannotDeleteLastWorkflowStateError()

        counts = await self._repo.issue_counts([state.id])
        issue_count = counts.get(state.id, 0)
        if issue_count > 0:
            if reassign_to_id is None:
                raise WorkflowStateHasIssuesError(details={"issue_count": issue_count})
            if reassign_to_id == state.id:
                raise InvalidReassignTargetError()
            target = await self._repo.get_by_id(workspace_id, reassign_to_id)
            if target is None:
                raise InvalidReassignTargetError()
            await self._repo.reassign_issues(state.id, target.id)

        # Soft delete primeiro: o índice único parcial `(workspace_id) WHERE
        # is_default AND deleted_at IS NULL` rejeitaria promover um novo
        # default enquanto o antigo ainda tem `is_default=True` e
        # `deleted_at IS NULL` ao mesmo tempo — soft delete tira o antigo do
        # escopo do índice antes da promoção tentar setar o novo.
        await self._repo.soft_delete(state.id)

        if state.is_default:
            promoted = next(s for s in remaining if s.id != state.id)
            promoted.is_default = True
            await self._repo.update(promoted)

    async def _clear_current_default(self, workspace_id: uuid.UUID) -> None:
        current_default = await self._repo.get_default(workspace_id)
        if current_default is not None:
            current_default.is_default = False
            await self._repo.update(current_default)

    async def _get_active_state(
        self, workspace_id: uuid.UUID, state_id: uuid.UUID
    ) -> WorkflowState:
        state = await self._repo.get_by_id(workspace_id, state_id)
        if state is None:
            raise WorkflowStateNotFoundError()
        return state
