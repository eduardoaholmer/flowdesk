import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.validators import validate_hex_color

_NAME_MIN_LENGTH = 1
_NAME_MAX_LENGTH = 50
_DESCRIPTION_MAX_LENGTH = 280


def _validate_name(value: str) -> str:
    stripped = value.strip()
    if len(stripped) < _NAME_MIN_LENGTH:
        raise ValueError("O nome da label não pode ser vazio.")
    if len(stripped) > _NAME_MAX_LENGTH:
        raise ValueError(f"O nome da label deve ter no máximo {_NAME_MAX_LENGTH} caracteres.")
    return stripped


def _validate_description(value: str) -> str:
    if len(value) > _DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"A descrição deve ter no máximo {_DESCRIPTION_MAX_LENGTH} caracteres.")
    return value


class LabelCreateRequest(BaseModel):
    name: str
    color: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return _validate_name(value)

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str) -> str:
        return validate_hex_color(value)

    @field_validator("description")
    @classmethod
    def _check_description(cls, value: str | None) -> str | None:
        return _validate_description(value) if value is not None else None


class LabelUpdateRequest(BaseModel):
    name: str | None = None
    color: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str | None) -> str | None:
        return _validate_name(value) if value is not None else None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return validate_hex_color(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def _check_description(cls, value: str | None) -> str | None:
        return _validate_description(value) if value is not None else None


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str
    description: str | None
    created_at: datetime
    updated_at: datetime
