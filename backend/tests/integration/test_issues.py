import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.features.issues.models import Issue, IssueLabel
from src.features.issues.repository import IssueRepository
from src.features.labels.models import Label
from src.features.teams.models import Team, WorkflowState
from src.features.teams.repository import TeamRepository
from src.features.workspaces.models import Workspace


async def test_issue_full_chain_relationships_load(
    db_session: AsyncSession, issue: Issue, team: Team, workflow_state: WorkflowState
) -> None:
    stmt = (
        select(Issue)
        .options(selectinload(Issue.team), selectinload(Issue.status))
        .where(Issue.id == issue.id)
    )
    loaded = await db_session.scalar(stmt)

    assert loaded is not None
    assert loaded.team.id == team.id
    assert loaded.status.id == workflow_state.id
    assert loaded.project_id is None
    assert loaded.version == 1
    assert loaded.number == 1


async def test_issue_number_unique_per_team(
    issue_repo: IssueRepository,
    team: Team,
    team_repo: TeamRepository,
    workflow_state: WorkflowState,
    workspace: Workspace,
    issue: Issue,
) -> None:
    with pytest.raises(IntegrityError):
        await issue_repo.create(
            Issue(
                workspace_id=workspace.id,
                team_id=team.id,
                number=issue.number,
                title="Outra issue com o mesmo número",
                status_id=workflow_state.id,
                creator_id=issue.creator_id,
            )
        )


async def test_add_and_remove_label_from_issue(
    db_session: AsyncSession, issue_repo: IssueRepository, issue: Issue, label: Label
) -> None:
    await issue_repo.add_label(issue.id, label.id)

    stmt = select(Issue).options(selectinload(Issue.label_links)).where(Issue.id == issue.id)
    loaded = await db_session.scalar(stmt)
    assert loaded is not None
    assert [link.label_id for link in loaded.label_links] == [label.id]

    await issue_repo.remove_label(issue.id, label.id)
    await db_session.flush()
    remaining = await db_session.scalar(
        select(IssueLabel).where(IssueLabel.issue_id == issue.id, IssueLabel.label_id == label.id)
    )
    assert remaining is None


async def test_issue_label_cascades_when_issue_hard_deleted(
    db_session: AsyncSession, issue_repo: IssueRepository, issue: Issue, label: Label
) -> None:
    """`ON DELETE CASCADE` só é exercitado em delete físico — issues normalmente são
    soft-deleted pela aplicação, mas a constraint precisa se provar correta mesmo
    assim (defesa em profundidade contra um hard delete acidental/administrativo).
    """
    await issue_repo.add_label(issue.id, label.id)
    await db_session.flush()

    await db_session.delete(issue)
    await db_session.flush()

    remaining = await db_session.scalar(select(IssueLabel).where(IssueLabel.issue_id == issue.id))
    assert remaining is None
