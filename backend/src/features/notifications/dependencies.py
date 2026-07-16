from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.features.notifications.repository import (
    NotificationRepository,
    NotificationRepositoryProtocol,
)
from src.features.notifications.service import NotificationService


def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(session)


def get_notification_service(
    notification_repo: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> NotificationService:
    return NotificationService(notification_repo)
