import uuid
from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.project_key import validate_project_key_format
from src.core.slug import validate_slug_format
from src.core.validators import validate_hex_color
from src.features.projects.models import Project, ProjectStatus

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
    key: str | None = None
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

    @field_validator("key")
    @classmethod
    def _check_key(cls, value: str | None) -> str | None:
        return validate_project_key_format(value) if value is not None else None

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
    key: str | None = None
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

    @field_validator("key")
    @classmethod
    def _check_key(cls, value: str | None) -> str | None:
        return validate_project_key_format(value) if value is not None else None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return validate_hex_color(value) if value is not None else None

    @field_validator("icon")
    @classmethod
    def _check_icon(cls, value: str | None) -> str | None:
        return _validate_icon(value) if value is not None else None


class ProjectMemberAddRequest(BaseModel):
    user_id: uuid.UUID


@dataclass(frozen=True)
class ProjectView:
    """Projeto + agregados calculados para a resposta (membros e progresso).

    O service devolve isto em vez do `Project` cru porque `member_ids`/contagens
    não são colunas do model — mantém o service devolvendo um DTO de domínio,
    nunca um schema de resposta HTTP (`CLAUDE.md` §5). O router monta o
    `ProjectResponse` via `from_project`.
    """

    project: Project
    member_ids: list[uuid.UUID]
    issue_count: int
    done_issue_count: int


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    slug: str
    key: str
    description: str | None
    icon: str | None
    color: str | None
    status: ProjectStatus
    target_date: date | None
    lead_id: uuid.UUID | None
    created_by: uuid.UUID
    member_ids: list[uuid.UUID]
    issue_count: int
    done_issue_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_project(
        cls,
        project: Project,
        *,
        member_ids: list[uuid.UUID],
        issue_count: int,
        done_issue_count: int,
    ) -> "ProjectResponse":
        return cls(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            slug=project.slug,
            key=project.key,
            description=project.description,
            icon=project.icon,
            color=project.color,
            status=project.status,
            target_date=project.target_date,
            lead_id=project.lead_id,
            created_by=project.created_by,
            member_ids=member_ids,
            issue_count=issue_count,
            done_issue_count=done_issue_count,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @classmethod
    def from_view(cls, view: ProjectView) -> "ProjectResponse":
        return cls.from_project(
            view.project,
            member_ids=view.member_ids,
            issue_count=view.issue_count,
            done_issue_count=view.done_issue_count,
        )
