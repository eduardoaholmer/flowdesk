import uuid

import pytest
from src.features.notifications.exceptions import NotificationNotFoundError
from src.features.notifications.models import NotificationType
from src.features.notifications.service import NotificationService

from tests.unit.features.notifications.fakes import FakeNotificationRepository


@pytest.fixture
def notification_repo() -> FakeNotificationRepository:
    return FakeNotificationRepository()


@pytest.fixture
def service(notification_repo: FakeNotificationRepository) -> NotificationService:
    return NotificationService(notification_repo)


async def test_notify_creates_notification(
    service: NotificationService, notification_repo: FakeNotificationRepository
) -> None:
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    notification = await service.notify(
        user_id=user_id,
        workspace_id=workspace_id,
        notification_type=NotificationType.MENTION,
        payload={"comment_id": "abc"},
    )

    assert notification.id in notification_repo.notifications
    assert notification.user_id == user_id
    assert notification.workspace_id == workspace_id
    assert notification.type == NotificationType.MENTION
    assert notification.read_at is None


async def test_list_for_user_returns_only_that_users_notifications(
    service: NotificationService,
) -> None:
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    await service.notify(
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )
    await service.notify(
        user_id=other_user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )

    notifications, total = await service.list_for_user(user_id, page=1, per_page=20, read=None)

    assert total == 1
    assert notifications[0].user_id == user_id


async def test_list_for_user_filters_by_read_status(service: NotificationService) -> None:
    user_id = uuid.uuid4()
    read_notification = await service.notify(
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.STATUS_CHANGE,
        payload={},
    )
    await service.notify(
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.STATUS_CHANGE,
        payload={},
    )
    await service.mark_read(user_id, read_notification.id)

    unread, unread_total = await service.list_for_user(user_id, page=1, per_page=20, read=False)
    read, read_total = await service.list_for_user(user_id, page=1, per_page=20, read=True)

    assert unread_total == 1
    assert unread[0].id != read_notification.id
    assert read_total == 1
    assert read[0].id == read_notification.id


async def test_list_for_user_paginates(service: NotificationService) -> None:
    user_id = uuid.uuid4()
    for _ in range(3):
        await service.notify(
            user_id=user_id,
            workspace_id=uuid.uuid4(),
            notification_type=NotificationType.ASSIGNMENT,
            payload={},
        )

    page, total = await service.list_for_user(user_id, page=1, per_page=2, read=None)

    assert total == 3
    assert len(page) == 2


async def test_mark_read_marks_notification_and_returns_it(
    service: NotificationService,
) -> None:
    user_id = uuid.uuid4()
    notification = await service.notify(
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )

    marked = await service.mark_read(user_id, notification.id)

    assert marked.read_at is not None


async def test_mark_read_is_idempotent(service: NotificationService) -> None:
    user_id = uuid.uuid4()
    notification = await service.notify(
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )

    first = await service.mark_read(user_id, notification.id)
    second = await service.mark_read(user_id, notification.id)

    assert first.read_at == second.read_at


async def test_mark_read_raises_not_found_for_missing_notification(
    service: NotificationService,
) -> None:
    with pytest.raises(NotificationNotFoundError):
        await service.mark_read(uuid.uuid4(), uuid.uuid4())


async def test_mark_read_raises_not_found_for_another_users_notification(
    service: NotificationService,
) -> None:
    owner_id = uuid.uuid4()
    notification = await service.notify(
        user_id=owner_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )

    with pytest.raises(NotificationNotFoundError):
        await service.mark_read(uuid.uuid4(), notification.id)


async def test_mark_all_read_marks_every_unread_notification_for_user(
    service: NotificationService,
) -> None:
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    for _ in range(2):
        await service.notify(
            user_id=user_id,
            workspace_id=uuid.uuid4(),
            notification_type=NotificationType.MENTION,
            payload={},
        )
    other_notification = await service.notify(
        user_id=other_user_id,
        workspace_id=uuid.uuid4(),
        notification_type=NotificationType.MENTION,
        payload={},
    )

    await service.mark_all_read(user_id)

    unread, unread_total = await service.list_for_user(user_id, page=1, per_page=20, read=False)
    assert unread_total == 0
    assert unread == []
    assert other_notification.read_at is None
