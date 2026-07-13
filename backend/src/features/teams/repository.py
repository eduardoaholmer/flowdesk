import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.teams.models import Team, TeamIssueCounter, TeamMember, WorkflowState


class TeamRepositoryProtocol(Protocol):
    async def create(self, team: Team) -> Team: ...
    async def get_by_id(self, workspace_id: uuid.UUID, team_id: uuid.UUID) -> Team | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Team]: ...
    async def add_member(self, member: TeamMember) -> TeamMember: ...
    async def list_workflow_states(self, team_id: uuid.UUID) -> Sequence[WorkflowState]: ...
    async def next_issue_number(self, team_id: uuid.UUID) -> int: ...


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, team: Team) -> Team:
        """Cria o time e já garante a linha de `TeamIssueCounter` correspondente —
        um time sem contador quebraria a numeração de issue na primeira criação.
        """
        self._session.add(team)
        await self._session.flush()
        self._session.add(TeamIssueCounter(team_id=team.id, next_number=1))
        await self._session.flush()
        return team

    async def get_by_id(self, workspace_id: uuid.UUID, team_id: uuid.UUID) -> Team | None:
        stmt = select(Team).where(
            Team.id == team_id, Team.workspace_id == workspace_id, Team.deleted_at.is_(None)
        )
        result: Team | None = await self._session.scalar(stmt)
        return result

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Team]:
        stmt = select(Team).where(Team.workspace_id == workspace_id, Team.deleted_at.is_(None))
        return (await self._session.scalars(stmt)).all()

    async def add_member(self, member: TeamMember) -> TeamMember:
        self._session.add(member)
        await self._session.flush()
        return member

    async def list_workflow_states(self, team_id: uuid.UUID) -> Sequence[WorkflowState]:
        stmt = (
            select(WorkflowState)
            .where(WorkflowState.team_id == team_id, WorkflowState.deleted_at.is_(None))
            .order_by(WorkflowState.position)
        )
        return (await self._session.scalars(stmt)).all()

    async def next_issue_number(self, team_id: uuid.UUID) -> int:
        """`SELECT ... FOR UPDATE` sobre o contador do time — já previsto em
        docs/03-database.md §8 para gerar `number` sequencial sem corrida/gap,
        sem depender de um `SERIAL` global.
        """
        stmt = select(TeamIssueCounter).where(TeamIssueCounter.team_id == team_id).with_for_update()
        counter = await self._session.scalar(stmt)
        if counter is None:
            raise ValueError(f"TeamIssueCounter ausente para o time {team_id}")

        issued_number = counter.next_number
        await self._session.execute(
            update(TeamIssueCounter)
            .where(TeamIssueCounter.team_id == team_id)
            .values(next_number=issued_number + 1)
        )
        return issued_number
