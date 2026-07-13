import pytest
from sqlalchemy.exc import IntegrityError
from src.features.attachments.models import Attachment
from src.features.attachments.repository import AttachmentRepository
from src.features.auth.models import User
from src.features.comments.models import Comment
from src.features.issues.models import Issue
from src.features.notifications.models import Notification, NotificationType
from src.features.notifications.repository import NotificationRepository
from src.features.workspaces.models import Workspace


async def test_create_and_mark_notification_read(
    notification_repo: NotificationRepository, workspace: Workspace, user: User
) -> None:
    notification = await notification_repo.create(
        Notification(
            user_id=user.id,
            workspace_id=workspace.id,
            type=NotificationType.MENTION,
            payload={"issue_id": "..."},
        )
    )
    assert notification.read_at is None

    unread = await notification_repo.list_unread_by_user(user.id)
    assert [n.id for n in unread] == [notification.id]

    await notification_repo.mark_read(notification.id)
    unread_after = await notification_repo.list_unread_by_user(user.id)
    assert unread_after == []


async def test_attachment_requires_exactly_one_parent(
    attachment_repo: AttachmentRepository, workspace: Workspace, user: User, issue: Issue
) -> None:
    valid = await attachment_repo.create(
        Attachment(
            workspace_id=workspace.id,
            issue_id=issue.id,
            uploader_id=user.id,
            file_name="print.png",
            content_type="image/png",
            file_size=1024,
            storage_key="attachments/print.png",
        )
    )
    assert valid.comment_id is None

    with pytest.raises(IntegrityError):
        await attachment_repo.create(
            Attachment(
                workspace_id=workspace.id,
                issue_id=None,
                comment_id=None,
                uploader_id=user.id,
                file_name="orphan.png",
                content_type="image/png",
                file_size=1024,
                storage_key="attachments/orphan.png",
            )
        )


async def test_attachment_rejects_both_parents_set(
    attachment_repo: AttachmentRepository,
    workspace: Workspace,
    user: User,
    issue: Issue,
    comment: Comment,
) -> None:
    with pytest.raises(IntegrityError):
        await attachment_repo.create(
            Attachment(
                workspace_id=workspace.id,
                issue_id=issue.id,
                comment_id=comment.id,
                uploader_id=user.id,
                file_name="both.png",
                content_type="image/png",
                file_size=1024,
                storage_key="attachments/both.png",
            )
        )
