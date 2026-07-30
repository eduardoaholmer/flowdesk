import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.teams.models import Team, TeamIssueCounter
from src.features.teams.repository import TeamRepository
from src.features.workspaces.models import Workspace


async def test_create_team_also_creates_issue_counter(db_session: AsyncSession, team: Team) -> None:
    stmt = select(TeamIssueCounter).where(TeamIssueCounter.team_id == team.id)
    counter = await db_session.scalar(stmt)

    assert counter is not None
    assert counter.next_number == 1


async def test_next_issue_number_increments_without_gaps(
    team_repo: TeamRepository, team: Team
) -> None:
    first = await team_repo.next_issue_number(team.id)
    second = await team_repo.next_issue_number(team.id)

    assert (first, second) == (1, 2)


async def test_key_unique_per_workspace_while_active(
    team_repo: TeamRepository, team: Team, workspace: Workspace
) -> None:
    with pytest.raises(IntegrityError):
        await team_repo.create(Team(workspace_id=workspace.id, name="Outro Time", key=team.key))
