import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.features.issues.models import IssuePriority, IssueStatus

_TITLE_MIN_LENGTH = 1
_TITLE_MAX_LENGTH = 255


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if len(stripped) < _TITLE_MIN_LENGTH:
        raise ValueError("O título da issue não pode ser vazio.")
    if len(stripped) > _TITLE_MAX_LENGTH:
        raise ValueError(f"O título da issue deve ter no máximo {_TITLE_MAX_LENGTH} caracteres.")
    return stripped


def _validate_estimate(value: int | None) -> int | None:
    if value is not None and value < 0:
        raise ValueError("A estimativa não pode ser negativa.")
    return value


class IssueCreateRequest(BaseModel):
    title: str
    description: str | None = None
    project_id: uuid.UUID | None = None
    status: IssueStatus = IssueStatus.BACKLOG
    priority: IssuePriority = IssuePriority.NO_PRIORITY
    assignee_id: uuid.UUID | None = None
    estimate: int | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def _check_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("estimate")
    @classmethod
    def _check_estimate(cls, value: int | None) -> int | None:
        return _validate_estimate(value)


class IssueUpdateRequest(BaseModel):
    """Atualização parcial — ao contrário de `ProjectUpdateRequest`, `status`
    *é* aceito aqui: mudança de status de issue é uma ação frequente e
    dirigida por board/board-like UI, não uma transição administrativa rara
    como arquivar/restaurar projeto (ver ADR-012, Decisão 1).
    """

    title: str | None = None
    description: str | None = None
    project_id: uuid.UUID | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: uuid.UUID | None = None
    estimate: int | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def _check_title(cls, value: str | None) -> str | None:
        return _validate_title(value) if value is not None else None

    @field_validator("estimate")
    @classmethod
    def _check_estimate(cls, value: int | None) -> int | None:
        return _validate_estimate(value)


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None
    identifier: str
    number: int
    title: str
    description: str | None
    status: IssueStatus
    priority: IssuePriority
    assignee_id: uuid.UUID | None
    creator_id: uuid.UUID
    estimate: int | None
    due_date: date | None
    version: int
    created_at: datetime
    updated_at: datetime


class IssueLabelAddRequest(BaseModel):
    label_id: uuid.UUID


class IssueActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime
