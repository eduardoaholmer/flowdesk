import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.notifications.models import Notification


class NotificationRepositoryProtocol(Protocol):
    async def create(self, notification: Notification) -> Notification: ...
    async def list_unread_by_user(self, user_id: uuid.UUID) -> Sequence[Notification]: ...
    async def mark_read(self, notification_id: uuid.UUID) -> None: ...


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, notification: Notification) -> Notification:
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_unread_by_user(self, user_id: uuid.UUID) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .order_by(Notification.created_at.desc())
        )
        return (await self._session.scalars(stmt)).all()

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read_at=datetime.now(UTC))
        )
