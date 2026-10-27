import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory

_NAME_MIN_LENGTH = 1
_NAME_MAX_LENGTH = 50


def _validate_name(value: str) -> str:
    stripped = value.strip()
    if len(stripped) < _NAME_MIN_LENGTH:
        raise ValueError("O nome do status não pode ser vazio.")
    if len(stripped) > _NAME_MAX_LENGTH:
        raise ValueError(f"O nome do status deve ter no máximo {_NAME_MAX_LENGTH} caracteres.")
    return stripped


class WorkflowStateCreateRequest(BaseModel):
    name: str
    category: WorkflowStateCategory
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return _validate_name(value)


class WorkflowStateUpdateRequest(BaseModel):
    name: str | None = None
    category: WorkflowStateCategory | None = None
    is_default: bool | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str | None) -> str | None:
        return _validate_name(value) if value is not None else None


class WorkflowStateReorderRequest(BaseModel):
    """Lista completa de IDs na nova ordem — o service valida que é exatamente
    o conjunto de status ativos do workspace, nem um a mais nem a menos."""

    ordered_ids: list[uuid.UUID]


@dataclass(frozen=True)
class WorkflowStateView:
    """`WorkflowState` + contagem de issues vinculadas — devolvido pelo service
    no lugar do model cru porque `issue_count` não é coluna (mesmo padrão de
    `LabelView`). O frontend usa a contagem para avisar o usuário antes de uma
    tentativa de exclusão que exigiria reatribuição."""

    workflow_state: WorkflowState
    issue_count: int


class WorkflowStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    category: WorkflowStateCategory
    position: int
    is_default: bool
    issue_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_view(cls, view: WorkflowStateView) -> "WorkflowStateResponse":
        state = view.workflow_state
        return cls(
            id=state.id,
            workspace_id=state.workspace_id,
            name=state.name,
            category=state.category,
            position=state.position,
            is_default=state.is_default,
            issue_count=view.issue_count,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )
