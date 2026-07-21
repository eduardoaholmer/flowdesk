import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.validators import validate_hex_color
from src.features.labels.models import Label

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


@dataclass(frozen=True)
class LabelView:
    """Label + contagem de issues que a carregam. Devolvido pelo service no lugar
    do `Label` cru porque `issue_count` não é coluna do model (mesmo racional de
    `ProjectView`) — mantém o service devolvendo DTO de domínio, não schema HTTP.
    """

    label: Label
    issue_count: int


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str
    description: str | None
    # Uso da label (nº de issues não deletadas que a carregam). Autoritativo
    # apenas quando construído via `from_view` (endpoints de Labels do workspace).
    # A listagem de labels *de uma issue* (`GET /issues/{id}/labels`) reaproveita
    # este schema como chips e deixa em 0 — ali a contagem global não é exibida.
    issue_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_view(cls, view: LabelView) -> "LabelResponse":
        label = view.label
        return cls(
            id=label.id,
            workspace_id=label.workspace_id,
            name=label.name,
            color=label.color,
            description=label.description,
            issue_count=view.issue_count,
            created_at=label.created_at,
            updated_at=label.updated_at,
        )
