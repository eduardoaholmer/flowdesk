import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.notifications.models import Notification


class NotificationRepositoryProtocol(Protocol):
    async def create(self, notification: Notification) -> Notification: ...
    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None: ...
    async def list_unread_by_user(self, user_id: uuid.UUID) -> Sequence[Notification]: ...
    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int, read: bool | None
    ) -> Sequence[Notification]: ...
    async def count_by_user(self, user_id: uuid.UUID, *, read: bool | None) -> int: ...
    async def mark_read(self, notification_id: uuid.UUID) -> None: ...
    async def mark_all_read(self, user_id: uuid.UUID) -> None: ...


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, notification: Notification) -> Notification:
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return await self._session.get(Notification, notification_id)

    async def list_unread_by_user(self, user_id: uuid.UUID) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .order_by(Notification.created_at.desc())
        )
        return (await self._session.scalars(stmt)).all()

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int, read: bool | None
    ) -> Sequence[Notification]:
        stmt = self._filtered(user_id, read=read).order_by(Notification.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        return (await self._session.scalars(stmt)).all()

    async def count_by_user(self, user_id: uuid.UUID, *, read: bool | None) -> int:
        stmt = select(func.count()).select_from(self._filtered(user_id, read=read).subquery())
        return (await self._session.scalar(stmt)) or 0

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read_at=datetime.now(UTC))
        )

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )

    def _filtered(self, user_id: uuid.UUID, *, read: bool | None) -> Select[tuple[Notification]]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if read is True:
            stmt = stmt.where(Notification.read_at.is_not(None))
        elif read is False:
            stmt = stmt.where(Notification.read_at.is_(None))
        return stmt
