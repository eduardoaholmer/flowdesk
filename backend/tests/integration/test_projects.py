import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.models import User
from src.features.issues.models import Issue, IssueStatus
from src.features.issues.repository import IssueRepository
from src.features.projects.models import Project, ProjectMember
from src.features.projects.repository import ProjectRepository
from src.features.workspaces.models import Workspace
from tests.integration.conftest import unique_suffix


@pytest.fixture
def project_repo(db_session: AsyncSession) -> ProjectRepository:
    return ProjectRepository(db_session)


async def _make_project(
    project_repo: ProjectRepository, workspace: Workspace, user: User, *, key: str, name: str
) -> Project:
    return await project_repo.create(
        Project(
            workspace_id=workspace.id,
            name=name,
            slug=f"{name.lower().replace(' ', '-')}-{unique_suffix()}",
            key=key,
            created_by=user.id,
        )
    )


async def test_key_unique_per_workspace_while_active(
    project_repo: ProjectRepository, workspace: Workspace, user: User
) -> None:
    await _make_project(project_repo, workspace, user, key="ABC", name="Alpha")

    with pytest.raises(IntegrityError):
        await _make_project(project_repo, workspace, user, key="ABC", name="Beta")


async def test_key_free_again_after_soft_delete(
    db_session: AsyncSession, project_repo: ProjectRepository, workspace: Workspace, user: User
) -> None:
    first = await _make_project(project_repo, workspace, user, key="ABC", name="Alpha")
    await project_repo.soft_delete(first.id)
    await db_session.flush()

    recreated = await _make_project(project_repo, workspace, user, key="ABC", name="Beta")

    assert recreated.id != first.id


async def test_add_member_is_idempotent_and_lists_ids(
    db_session: AsyncSession, project_repo: ProjectRepository, workspace: Workspace, user: User
) -> None:
    project = await _make_project(project_repo, workspace, user, key="ABC", name="Alpha")

    first = await project_repo.add_member(
        ProjectMember(workspace_id=workspace.id, project_id=project.id, user_id=user.id)
    )
    second = await project_repo.add_member(
        ProjectMember(workspace_id=workspace.id, project_id=project.id, user_id=user.id)
    )
    await db_session.flush()

    assert first is True
    assert second is False
    members = await project_repo.list_member_ids([project.id])
    assert members[project.id] == [user.id]


async def test_remove_member_reports_whether_removed(
    db_session: AsyncSession, project_repo: ProjectRepository, workspace: Workspace, user: User
) -> None:
    project = await _make_project(project_repo, workspace, user, key="ABC", name="Alpha")
    await project_repo.add_member(
        ProjectMember(workspace_id=workspace.id, project_id=project.id, user_id=user.id)
    )
    await db_session.flush()

    assert await project_repo.remove_member(project.id, user.id) is True
    assert await project_repo.remove_member(project.id, user.id) is False


async def test_issue_counts_aggregates_total_and_done(
    db_session: AsyncSession,
    project_repo: ProjectRepository,
    issue_repo: IssueRepository,
    workspace: Workspace,
    user: User,
) -> None:
    project = await _make_project(project_repo, workspace, user, key="ABC", name="Alpha")
    for status in (IssueStatus.TODO, IssueStatus.DONE, IssueStatus.DONE):
        number = await issue_repo.next_number(workspace.id)
        await issue_repo.create(
            Issue(
                workspace_id=workspace.id,
                project_id=project.id,
                number=number,
                title="t",
                status=status,
                creator_id=user.id,
            )
        )
    # Issue deletada não entra na contagem.
    number = await issue_repo.next_number(workspace.id)
    deleted = await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            project_id=project.id,
            number=number,
            title="t",
            status=IssueStatus.TODO,
            creator_id=user.id,
        )
    )
    await issue_repo.soft_delete(deleted.id)
    await db_session.flush()

    counts = await project_repo.issue_counts([project.id])

    assert counts[project.id] == (3, 2)
