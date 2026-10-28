import uuid
from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.features.issues.models import ActivityActorSource, IssuePriority

_TITLE_MIN_LENGTH = 1
_TITLE_MAX_LENGTH = 255
_MIN_DUE_DATE = date(1900, 1, 1)
_MAX_DUE_DATE = date(2200, 12, 31)
_MAX_LABELS_ON_CREATE = 20


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


def _validate_due_date(value: date | None) -> date | None:
    if value is not None and not (_MIN_DUE_DATE <= value <= _MAX_DUE_DATE):
        raise ValueError(
            f"A data de vencimento deve estar entre {_MIN_DUE_DATE.isoformat()} "
            f"e {_MAX_DUE_DATE.isoformat()}."
        )
    return value


class IssueCreateRequest(BaseModel):
    """`status_id` opcional: quando omitido, o service atribui o status
    marcado `is_default` no workspace (ver `WorkflowStateService.seed_defaults`,
    Sprint 9.2/ADR-056) — sem valor fixo aqui, já que o status default agora é
    dado de workspace, não uma constante do código.

    `label_ids` aplica labels já na criação, na mesma transação (ADR-064) — sem
    isso o frontend teria de criar a issue e depois chamar
    `POST /issues/{id}/labels` uma vez por label, deixando a issue sem parte das
    labels se uma dessas chamadas falhasse."""

    title: str
    description: str | None = None
    project_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    priority: IssuePriority = IssuePriority.NO_PRIORITY
    assignee_id: uuid.UUID | None = None
    estimate: int | None = None
    due_date: date | None = None
    label_ids: list[uuid.UUID] = Field(default_factory=list, max_length=_MAX_LABELS_ON_CREATE)

    @field_validator("title")
    @classmethod
    def _check_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("label_ids")
    @classmethod
    def _dedupe_label_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        return list(dict.fromkeys(value))

    @field_validator("estimate")
    @classmethod
    def _check_estimate(cls, value: int | None) -> int | None:
        return _validate_estimate(value)

    @field_validator("due_date")
    @classmethod
    def _check_due_date(cls, value: date | None) -> date | None:
        return _validate_due_date(value)


class IssueUpdateRequest(BaseModel):
    """Atualização parcial — ao contrário de `ProjectUpdateRequest`, `status`
    *é* aceito aqui: mudança de status de issue é uma ação frequente e
    dirigida por board/board-like UI, não uma transição administrativa rara
    como arquivar/restaurar projeto (ver ADR-012, Decisão 1).

    `parent_id`, como `due_date` (ADR-055/Sprint 23.1), precisa distinguir
    "campo omitido" (preserva o vínculo atual) de "`null` explícito"
    (desvincula) — o service checa `model_fields_set`, não `is not None`.
    O mesmo vale para os demais campos anuláveis da issue (`description`,
    `project_id`, `assignee_id`, `estimate`); `title`, `status_id` e
    `priority` não aceitam ficar vazios, então `null` neles é ignorado.
    """

    title: str | None = None
    description: str | None = None
    project_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
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

    @field_validator("due_date")
    @classmethod
    def _check_due_date(cls, value: date | None) -> date | None:
        return _validate_due_date(value)


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    identifier: str
    number: int
    title: str
    description: str | None
    status_id: uuid.UUID
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
    actor_id: uuid.UUID | None
    actor_source: ActivityActorSource
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime


@dataclass(frozen=True)
class AutomationActor:
    """Quem aparece como autor de uma mudança feita por automação (Sprint 10.4).
    `user_id` é o membro do workspace correspondente, quando existe; `name` é o que
    vai na notificação ("Ada via GitHub" ou só "GitHub")."""

    source: ActivityActorSource
    user_id: uuid.UUID | None
    name: str
