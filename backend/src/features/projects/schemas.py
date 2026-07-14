import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.slug import validate_slug_format
from src.core.validators import validate_hex_color
from src.features.projects.models import ProjectStatus

_ICON_MAX_LENGTH = 64
_NAME_MIN_LENGTH = 2
_NAME_MAX_LENGTH = 100


def _validate_name(value: str) -> str:
    stripped = value.strip()
    if len(stripped) < _NAME_MIN_LENGTH:
        raise ValueError(f"O nome do projeto deve ter ao menos {_NAME_MIN_LENGTH} caracteres.")
    if len(stripped) > _NAME_MAX_LENGTH:
        raise ValueError(f"O nome do projeto deve ter no máximo {_NAME_MAX_LENGTH} caracteres.")
    return stripped


def _validate_icon(value: str) -> str:
    if len(value) > _ICON_MAX_LENGTH:
        raise ValueError(f"O ícone deve ter no máximo {_ICON_MAX_LENGTH} caracteres.")
    return value


class ProjectCreateRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    target_date: date | None = None
    lead_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return _validate_name(value)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str | None) -> str | None:
        return validate_slug_format(value) if value is not None else None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return validate_hex_color(value) if value is not None else None

    @field_validator("icon")
    @classmethod
    def _check_icon(cls, value: str | None) -> str | None:
        return _validate_icon(value) if value is not None else None


class ProjectUpdateRequest(BaseModel):
    """Sem campo `status`: a única forma de transicionar o status de um projeto
    é `POST .../archive` ou `POST .../restore` — mantém a transição de estado
    como uma ação de negócio explícita e auditável, não um valor arbitrário que
    um `PATCH` genérico poderia setar (CLAUDE.md §4, "atualizar apenas os
    campos autorizados").
    """

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    target_date: date | None = None
    lead_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str | None) -> str | None:
        return _validate_name(value) if value is not None else None

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str | None) -> str | None:
        return validate_slug_format(value) if value is not None else None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return validate_hex_color(value) if value is not None else None

    @field_validator("icon")
    @classmethod
    def _check_icon(cls, value: str | None) -> str | None:
        return _validate_icon(value) if value is not None else None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    icon: str | None
    color: str | None
    status: ProjectStatus
    target_date: date | None
    lead_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
