import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import column, func, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.workflow_states.models import WorkflowState

# Referência Core (não ORM) à tabela `issues` — mesmo racional de
# `ProjectRepository._issues_table` (features/projects/repository.py): evita
# importar o model `Issue` aqui, o que acoplaria `WorkflowState` ao grafo de
# mappers da feature Issues (incluindo seu relationship com `Comment`) só para
# contar/reatribuir por `status_id`.
_issues_table = table("issues", column("id"), column("status_id"), column("deleted_at"))


class WorkflowStateRepositoryProtocol(Protocol):
    async def create(self, state: WorkflowState) -> WorkflowState: ...
    async def get_by_id(
        self, workspace_id: uuid.UUID, state_id: uuid.UUID
    ) -> WorkflowState | None: ...
    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> WorkflowState | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[WorkflowState]: ...
    async def get_default(self, workspace_id: uuid.UUID) -> WorkflowState | None: ...
    async def max_position(self, workspace_id: uuid.UUID) -> int | None: ...
    async def issue_counts(self, state_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]: ...
    async def reassign_issues(self, from_status_id: uuid.UUID, to_status_id: uuid.UUID) -> None: ...
    async def update(self, state: WorkflowState) -> WorkflowState: ...
    async def soft_delete(self, state_id: uuid.UUID) -> None: ...


class WorkflowStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, state: WorkflowState) -> WorkflowState:
        self._session.add(state)
        await self._session.flush()
        return state

    async def get_by_id(self, workspace_id: uuid.UUID, state_id: uuid.UUID) -> WorkflowState | None:
        stmt = select(WorkflowState).where(
            WorkflowState.id == state_id,
            WorkflowState.workspace_id == workspace_id,
            WorkflowState.deleted_at.is_(None),
        )
        result: WorkflowState | None = await self._session.scalar(stmt)
        return result

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> WorkflowState | None:
        stmt = select(WorkflowState).where(
            WorkflowState.workspace_id == workspace_id,
            WorkflowState.name == name,
            WorkflowState.deleted_at.is_(None),
        )
        result: WorkflowState | None = await self._session.scalar(stmt)
        return result

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[WorkflowState]:
        stmt = (
            select(WorkflowState)
            .where(WorkflowState.workspace_id == workspace_id, WorkflowState.deleted_at.is_(None))
            .order_by(WorkflowState.position.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def get_default(self, workspace_id: uuid.UUID) -> WorkflowState | None:
        stmt = select(WorkflowState).where(
            WorkflowState.workspace_id == workspace_id,
            WorkflowState.is_default.is_(True),
            WorkflowState.deleted_at.is_(None),
        )
        result: WorkflowState | None = await self._session.scalar(stmt)
        return result

    async def max_position(self, workspace_id: uuid.UUID) -> int | None:
        stmt = select(func.max(WorkflowState.position)).where(
            WorkflowState.workspace_id == workspace_id, WorkflowState.deleted_at.is_(None)
        )
        result: int | None = await self._session.scalar(stmt)
        return result

    async def issue_counts(self, state_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
        counts: dict[uuid.UUID, int] = {state_id: 0 for state_id in state_ids}
        if not state_ids:
            return counts
        stmt = (
            select(_issues_table.c.status_id, func.count())
            .where(_issues_table.c.status_id.in_(state_ids), _issues_table.c.deleted_at.is_(None))
            .group_by(_issues_table.c.status_id)
        )
        for status_id, count in (await self._session.execute(stmt)).all():
            counts[status_id] = count
        return counts

    async def reassign_issues(self, from_status_id: uuid.UUID, to_status_id: uuid.UUID) -> None:
        stmt = (
            update(_issues_table)
            .where(_issues_table.c.status_id == from_status_id)
            .values(status_id=to_status_id)
        )
        await self._session.execute(stmt)

    async def update(self, state: WorkflowState) -> WorkflowState:
        await self._session.flush()
        return state

    async def soft_delete(self, state_id: uuid.UUID) -> None:
        await self._session.execute(
            update(WorkflowState)
            .where(WorkflowState.id == state_id)
            .values(deleted_at=datetime.now(UTC))
        )
