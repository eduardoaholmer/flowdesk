import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

_BODY_MIN_LENGTH = 1
_BODY_MAX_LENGTH = 10_000


def _validate_body(value: str) -> str:
    stripped = value.strip()
    if len(stripped) < _BODY_MIN_LENGTH:
        raise ValueError("O comentário não pode ser vazio.")
    if len(stripped) > _BODY_MAX_LENGTH:
        raise ValueError(f"O comentário deve ter no máximo {_BODY_MAX_LENGTH} caracteres.")
    return stripped


class CommentCreateRequest(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def _check_body(cls, value: str) -> str:
        return _validate_body(value)


class CommentUpdateRequest(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def _check_body(cls, value: str) -> str:
        return _validate_body(value)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    issue_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    mentioned_user_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
