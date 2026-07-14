import uuid

import pytest
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser
from src.features.comments.schemas import CommentCreateRequest, CommentUpdateRequest
from src.features.comments.service import CommentService
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.schemas import IssueCreateRequest
from src.features.issues.service import IssueService
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole

from tests.unit.features.comments.fakes import FakeCommentRepository
from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.labels.fakes import FakeLabelRepository
from tests.unit.features.projects.fakes import FakeProjectRepository
from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository


def _user(email: str = "ada@example.com", name: str = "Ada Lovelace") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name=name)


def _member(workspace_id: uuid.UUID, user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)


class _FakeUser:
    def __init__(self, email: str) -> None:
        self.email = email


@pytest.fixture
def comment_repo() -> FakeCommentRepository:
    return FakeCommentRepository()


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def workspace_repo() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def service(
    comment_repo: FakeCommentRepository,
    issue_repo: FakeIssueRepository,
    workspace_repo: FakeWorkspaceRepository,
) -> CommentService:
    return CommentService(comment_repo, issue_repo, workspace_repo, PermissionService())


async def _create_issue(issue_repo: FakeIssueRepository, workspace_id: uuid.UUID) -> uuid.UUID:
    issue_service = IssueService(
        issue_repo, PermissionService(), FakeProjectRepository(), FakeLabelRepository()
    )
    issue = await issue_service.create(_user(), workspace_id, IssueCreateRequest(title="Issue"))
    return issue.id


def _add_member(
    workspace_repo: FakeWorkspaceRepository,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    email: str,
) -> None:
    member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=WorkspaceRole.MEMBER)
    member.user = _FakeUser(email)
    workspace_repo.members[uuid.uuid4()] = member


async def test_create_raises_not_found_for_missing_issue(service: CommentService) -> None:
    with pytest.raises(IssueNotFoundError):
        await service.create(_user(), uuid.uuid4(), uuid.uuid4(), CommentCreateRequest(body="oi"))


async def test_create_records_activity_on_issue(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    issue_repo.activity_log.clear()

    comment = await service.create(
        _user(), workspace_id, issue_id, CommentCreateRequest(body="Primeiro comentário")
    )

    assert comment.issue_id == issue_id
    assert any(entry.action == "comment.created" for entry in issue_repo.activity_log)


async def test_create_detects_and_stores_mentions(
    service: CommentService,
    issue_repo: FakeIssueRepository,
    workspace_repo: FakeWorkspaceRepository,
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    mentioned_user_id = uuid.uuid4()
    _add_member(workspace_repo, workspace_id, mentioned_user_id, "grace@example.com")

    comment = await service.create(
        _user(),
        workspace_id,
        issue_id,
        CommentCreateRequest(body="Olá @grace, pode revisar?"),
    )

    assert comment.mentioned_user_ids == [mentioned_user_id]


async def test_create_ignores_mention_with_no_matching_member(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)

    comment = await service.create(
        _user(), workspace_id, issue_id, CommentCreateRequest(body="Olá @ninguem")
    )

    assert comment.mentioned_user_ids == []


async def test_list_for_issue_paginates(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    for i in range(3):
        await service.create(_user(), workspace_id, issue_id, CommentCreateRequest(body=f"c{i}"))

    page, total = await service.list_for_issue(workspace_id, issue_id, page=1, per_page=2)

    assert total == 3
    assert len(page) == 2
    assert [c.body for c in page] == ["c0", "c1"]


async def test_update_by_author_succeeds_via_ownership_override(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    author = _user()
    comment = await service.create(author, workspace_id, issue_id, CommentCreateRequest(body="oi"))
    author_member = _member(workspace_id, author.id, WorkspaceRole.MEMBER)

    updated = await service.update(
        author_member, workspace_id, comment.id, CommentUpdateRequest(body="editado")
    )

    assert updated.body == "editado"
    assert any(entry.action == "comment.updated" for entry in issue_repo.activity_log)


async def test_update_by_non_author_member_raises_permission_denied(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    author = _user()
    comment = await service.create(author, workspace_id, issue_id, CommentCreateRequest(body="oi"))
    other_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.MEMBER)

    with pytest.raises(PermissionDeniedError):
        await service.update(
            other_member, workspace_id, comment.id, CommentUpdateRequest(body="hijack")
        )


async def test_delete_by_admin_succeeds_without_being_author(
    service: CommentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    author = _user()
    comment = await service.create(author, workspace_id, issue_id, CommentCreateRequest(body="oi"))
    admin_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.ADMIN)

    await service.delete(admin_member, workspace_id, comment.id)

    assert any(entry.action == "comment.deleted" for entry in issue_repo.activity_log)
