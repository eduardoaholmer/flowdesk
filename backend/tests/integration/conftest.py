import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.attachments.repository import AttachmentRepository
from src.features.auth.models import User
from src.features.auth.repository import SessionRepository, UserRepository
from src.features.comments.models import Comment
from src.features.comments.repository import CommentRepository
from src.features.issues.models import Issue, IssuePriority
from src.features.issues.repository import IssueRepository
from src.features.labels.models import Label
from src.features.labels.repository import LabelRepository
from src.features.notifications.repository import NotificationRepository
from src.features.teams.models import Team, WorkflowState, WorkflowStateCategory
from src.features.teams.repository import TeamRepository
from src.features.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from src.features.workspaces.repository import InvitationRepository, WorkspaceRepository


def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def user_repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest.fixture
def session_repo(db_session: AsyncSession) -> SessionRepository:
    return SessionRepository(db_session)


@pytest.fixture
def workspace_repo(db_session: AsyncSession) -> WorkspaceRepository:
    return WorkspaceRepository(db_session)


@pytest.fixture
def invitation_repo(db_session: AsyncSession) -> InvitationRepository:
    return InvitationRepository(db_session)


@pytest.fixture
def team_repo(db_session: AsyncSession) -> TeamRepository:
    return TeamRepository(db_session)


@pytest.fixture
def label_repo(db_session: AsyncSession) -> LabelRepository:
    return LabelRepository(db_session)


@pytest.fixture
def issue_repo(db_session: AsyncSession) -> IssueRepository:
    return IssueRepository(db_session)


@pytest.fixture
def comment_repo(db_session: AsyncSession) -> CommentRepository:
    return CommentRepository(db_session)


@pytest.fixture
def notification_repo(db_session: AsyncSession) -> NotificationRepository:
    return NotificationRepository(db_session)


@pytest.fixture
def attachment_repo(db_session: AsyncSession) -> AttachmentRepository:
    return AttachmentRepository(db_session)


@pytest.fixture
async def user(user_repo: UserRepository) -> User:
    return await user_repo.create(
        User(
            name="Ada Lovelace",
            email=f"ada-{unique_suffix()}@example.com",
            password_hash="not-a-real-hash",
        )
    )


@pytest.fixture
async def workspace(workspace_repo: WorkspaceRepository, user: User) -> Workspace:
    ws = await workspace_repo.create(
        Workspace(name="Acme", slug=f"acme-{unique_suffix()}", owner_id=user.id)
    )
    await workspace_repo.add_member(
        WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.OWNER)
    )
    return ws


@pytest.fixture
async def team(team_repo: TeamRepository, workspace: Workspace) -> Team:
    return await team_repo.create(
        Team(workspace_id=workspace.id, name="Engenharia", key=f"ENG{unique_suffix()[:4].upper()}")
    )


@pytest.fixture
async def workflow_state(db_session: AsyncSession, team: Team) -> WorkflowState:
    state = WorkflowState(
        team_id=team.id,
        workspace_id=team.workspace_id,
        name="Todo",
        category=WorkflowStateCategory.UNSTARTED,
        position=1,
        is_default=True,
    )
    db_session.add(state)
    await db_session.flush()
    return state


@pytest.fixture
async def label(label_repo: LabelRepository, workspace: Workspace) -> Label:
    return await label_repo.create(Label(workspace_id=workspace.id, name="bug", color="#ff0000"))


@pytest.fixture
async def issue(
    issue_repo: IssueRepository,
    team_repo: TeamRepository,
    team: Team,
    workflow_state: WorkflowState,
    workspace: Workspace,
    user: User,
) -> Issue:
    number = await team_repo.next_issue_number(team.id)
    return await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            team_id=team.id,
            number=number,
            title="Corrigir bug de login",
            status_id=workflow_state.id,
            priority=IssuePriority.MEDIUM,
            creator_id=user.id,
        )
    )


@pytest.fixture
async def comment(comment_repo: CommentRepository, issue: Issue, user: User) -> Comment:
    return await comment_repo.create(
        Comment(workspace_id=issue.workspace_id, issue_id=issue.id, author_id=user.id, body="oi")
    )
