import io
import uuid

import pytest
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser
from src.features.attachments.exceptions import (
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    AttachmentTypeNotAllowedError,
)
from src.features.attachments.service import AttachmentService
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.schemas import IssueCreateRequest
from src.features.issues.service import IssueService
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole

from tests.unit.features.attachments.fakes import FakeAttachmentRepository, FakeStorageProvider
from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.labels.fakes import FakeLabelRepository
from tests.unit.features.projects.fakes import FakeProjectRepository

_ALLOWED_TYPES = frozenset({"image/png", "application/pdf"})
_MAX_SIZE = 1024


def _user() -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email="ada@example.com", name="Ada Lovelace")


def _member(workspace_id: uuid.UUID, user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)


@pytest.fixture
def attachment_repo() -> FakeAttachmentRepository:
    return FakeAttachmentRepository()


@pytest.fixture
def storage() -> FakeStorageProvider:
    return FakeStorageProvider()


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def service(
    attachment_repo: FakeAttachmentRepository,
    storage: FakeStorageProvider,
    issue_repo: FakeIssueRepository,
) -> AttachmentService:
    return AttachmentService(
        attachment_repo,
        issue_repo,
        storage,
        PermissionService(),
        max_size_bytes=_MAX_SIZE,
        allowed_content_types=_ALLOWED_TYPES,
    )


async def _create_issue(issue_repo: FakeIssueRepository, workspace_id: uuid.UUID) -> uuid.UUID:
    issue_service = IssueService(
        issue_repo, PermissionService(), FakeProjectRepository(), FakeLabelRepository()
    )
    issue = await issue_service.create(_user(), workspace_id, IssueCreateRequest(title="Issue"))
    return issue.id


async def test_upload_raises_not_found_for_missing_issue(service: AttachmentService) -> None:
    with pytest.raises(IssueNotFoundError):
        await service.upload_to_issue(
            _user(),
            uuid.uuid4(),
            uuid.uuid4(),
            file_name="print.png",
            content_type="image/png",
            size=10,
            stream=io.BytesIO(b"data"),
        )


async def test_upload_persists_attachment_and_records_activity(
    service: AttachmentService, issue_repo: FakeIssueRepository, storage: FakeStorageProvider
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)

    attachment = await service.upload_to_issue(
        _user(),
        workspace_id,
        issue_id,
        file_name="print.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )

    assert attachment.issue_id == issue_id
    assert attachment.storage_provider == "fake"
    assert attachment.storage_key in storage.saved
    assert any(entry.action == "attachment.uploaded" for entry in issue_repo.activity_log)


async def test_upload_rejects_file_too_large(
    service: AttachmentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)

    with pytest.raises(AttachmentTooLargeError):
        await service.upload_to_issue(
            _user(),
            workspace_id,
            issue_id,
            file_name="huge.png",
            content_type="image/png",
            size=_MAX_SIZE + 1,
            stream=io.BytesIO(b"x" * 10),
        )


async def test_upload_rejects_disallowed_content_type(
    service: AttachmentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)

    with pytest.raises(AttachmentTypeNotAllowedError):
        await service.upload_to_issue(
            _user(),
            workspace_id,
            issue_id,
            file_name="script.exe",
            content_type="application/x-msdownload",
            size=10,
            stream=io.BytesIO(b"x" * 10),
        )


async def test_list_for_issue_returns_only_that_issues_attachments(
    service: AttachmentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    other_issue_id = await _create_issue(issue_repo, workspace_id)
    await service.upload_to_issue(
        _user(),
        workspace_id,
        issue_id,
        file_name="print.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )
    await service.upload_to_issue(
        _user(),
        workspace_id,
        other_issue_id,
        file_name="other.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )

    attachments = await service.list_for_issue(workspace_id, issue_id)

    assert len(attachments) == 1
    assert attachments[0].issue_id == issue_id


async def test_get_raises_not_found_across_workspaces(
    service: AttachmentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    attachment = await service.upload_to_issue(
        _user(),
        workspace_id,
        issue_id,
        file_name="print.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )

    with pytest.raises(AttachmentNotFoundError):
        await service.get(uuid.uuid4(), attachment.id)


async def test_delete_by_uploader_succeeds_via_ownership_override(
    service: AttachmentService,
    issue_repo: FakeIssueRepository,
    storage: FakeStorageProvider,
    attachment_repo: FakeAttachmentRepository,
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    uploader = _user()
    attachment = await service.upload_to_issue(
        uploader,
        workspace_id,
        issue_id,
        file_name="print.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )
    uploader_member = _member(workspace_id, uploader.id, WorkspaceRole.MEMBER)

    await service.delete(uploader_member, workspace_id, attachment.id)

    assert attachment_repo.attachments[attachment.id].deleted_at is not None
    assert attachment.storage_key in storage.deleted
    assert any(entry.action == "attachment.deleted" for entry in issue_repo.activity_log)


async def test_delete_by_non_uploader_member_raises_permission_denied(
    service: AttachmentService, issue_repo: FakeIssueRepository
) -> None:
    workspace_id = uuid.uuid4()
    issue_id = await _create_issue(issue_repo, workspace_id)
    attachment = await service.upload_to_issue(
        _user(),
        workspace_id,
        issue_id,
        file_name="print.png",
        content_type="image/png",
        size=4,
        stream=io.BytesIO(b"data"),
    )
    other_member = _member(workspace_id, uuid.uuid4(), WorkspaceRole.MEMBER)

    with pytest.raises(PermissionDeniedError):
        await service.delete(other_member, workspace_id, attachment.id)
