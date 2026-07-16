import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.features.notifications.models import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    type: NotificationType
    payload: dict[str, object]
    read_at: datetime | None
    created_at: datetime
