import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    issue_id: uuid.UUID | None
    comment_id: uuid.UUID | None
    uploader_id: uuid.UUID
    file_name: str
    content_type: str
    file_size: int
    storage_provider: str
    created_at: datetime
