import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.notifications.models import Notification
from uuid6 import uuid7


class FakeNotificationRepository:
    """Implementa `NotificationRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/labels/fakes.py`.
    """

    def __init__(self) -> None:
        self.notifications: dict[uuid.UUID, Notification] = {}

    async def create(self, notification: Notification) -> Notification:
        if notification.id is None:
            notification.id = uuid7()
        notification.created_at = notification.created_at or datetime.now(UTC)
        self.notifications[notification.id] = notification
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return self.notifications.get(notification_id)

    async def list_unread_by_user(self, user_id: uuid.UUID) -> Sequence[Notification]:
        return await self.list_by_user(user_id, page=1, per_page=1000, read=False)

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int, read: bool | None
    ) -> Sequence[Notification]:
        matches = self._filtered(user_id, read=read)
        matches.sort(key=lambda n: n.created_at, reverse=True)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_user(self, user_id: uuid.UUID, *, read: bool | None) -> int:
        return len(self._filtered(user_id, read=read))

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        notification = self.notifications.get(notification_id)
        if notification is not None:
            notification.read_at = datetime.now(UTC)

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        for notification in self.notifications.values():
            if notification.user_id == user_id and notification.read_at is None:
                notification.read_at = datetime.now(UTC)

    def _filtered(self, user_id: uuid.UUID, *, read: bool | None) -> list[Notification]:
        matches = [n for n in self.notifications.values() if n.user_id == user_id]
        if read is True:
            matches = [n for n in matches if n.read_at is not None]
        elif read is False:
            matches = [n for n in matches if n.read_at is None]
        return matches
