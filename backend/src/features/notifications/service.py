import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.notifications.exceptions import NotificationNotFoundError
from src.features.notifications.models import Notification, NotificationType
from src.features.notifications.repository import NotificationRepositoryProtocol


class NotificationService:
    def __init__(self, notification_repo: NotificationRepositoryProtocol) -> None:
        self._notification_repo = notification_repo

    async def notify(
        self,
        *,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        notification_type: NotificationType,
        payload: dict[str, object],
    ) -> Notification:
        """Chamado pelo *service* público de outra feature como efeito colateral de
        uma ação de domínio (`docs/02-architecture.md` — ex.: `CommentService`
        notifica uma menção, `IssueService` notifica mudança de status) — nunca
        pelo repository de outra feature, nunca por um router diretamente.
        """
        return await self._notification_repo.create(
            Notification(
                user_id=user_id,
                workspace_id=workspace_id,
                type=notification_type,
                payload=payload,
            )
        )

    async def list_for_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int, read: bool | None
    ) -> tuple[Sequence[Notification], int]:
        notifications = await self._notification_repo.list_by_user(
            user_id, page=page, per_page=per_page, read=read
        )
        total = await self._notification_repo.count_by_user(user_id, read=read)
        return notifications, total

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        notification = await self._get_owned_notification(user_id, notification_id)
        if notification.read_at is None:
            await self._notification_repo.mark_read(notification_id)
            notification.read_at = datetime.now(UTC)
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self._notification_repo.mark_all_read(user_id)

    async def _get_owned_notification(
        self, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification:
        notification = await self._notification_repo.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            raise NotificationNotFoundError()
        return notification
