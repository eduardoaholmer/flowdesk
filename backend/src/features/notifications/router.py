import uuid

from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies import get_current_user
from src.core.schemas import CollectionEnvelope, DataEnvelope, PaginationMeta
from src.core.security import CurrentUser
from src.features.notifications.dependencies import get_notification_service
from src.features.notifications.schemas import NotificationResponse
from src.features.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=CollectionEnvelope[NotificationResponse])
async def list_notifications(
    read: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> CollectionEnvelope[NotificationResponse]:
    notifications, total = await service.list_for_user(
        current_user.id, page=page, per_page=per_page, read=read
    )
    return CollectionEnvelope(
        data=[NotificationResponse.model_validate(n) for n in notifications],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.patch("/{notification_id}", response_model=DataEnvelope[NotificationResponse])
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> DataEnvelope[NotificationResponse]:
    notification = await service.mark_read(current_user.id, notification_id)
    return DataEnvelope(data=NotificationResponse.model_validate(notification))


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> None:
    await service.mark_all_read(current_user.id)
