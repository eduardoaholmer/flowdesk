import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from sqlalchemy import Select, column, func, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.projects.models import Project, ProjectActivityLog, ProjectStatus

# Referência Core (não ORM) à tabela `issues` — só o suficiente para uma
# checagem de existência (`has_active_issues`). Importar o model `Issue`
# aqui obrigaria o SQLAlchemy a configurar o mapper inteiro de `Issue`
# (incluindo seu relationship com `Comment`) assim que `ProjectRepository`
# fosse carregado — acoplando Projects ao grafo de mappers de uma feature
# (Issues/Comments) que ainda nem está registrada em `main.py` nesta sprint.
# `sqlalchemy.table()`/`column()` consultam por nome de coluna sem passar
# pelo registry declarativo, evitando esse acoplamento por completo.
_issues_table = table("issues", column("project_id"), column("deleted_at"))

ProjectSort = Literal[
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "target_date",
    "-target_date",
]

_SORT_COLUMNS: dict[str, Any] = {
    "name": Project.name,
    "created_at": Project.created_at,
    "updated_at": Project.updated_at,
    "target_date": Project.target_date,
}


def _order_by_clause(sort: ProjectSort) -> Any:
    field = sort[1:] if sort.startswith("-") else sort
    column = _SORT_COLUMNS[field]
    return column.desc() if sort.startswith("-") else column.asc()


class ProjectRepositoryProtocol(Protocol):
    async def create(self, project: Project) -> Project: ...
    async def get_by_id(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project | None: ...
    async def get_by_slug(self, workspace_id: uuid.UUID, slug: str) -> Project | None: ...
    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Project | None: ...
    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        status: ProjectStatus | None = None,
        sort: ProjectSort = "-created_at",
    ) -> Sequence[Project]: ...
    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        search: str | None = None,
        status: ProjectStatus | None = None,
    ) -> int: ...
    async def update(self, project: Project) -> Project: ...
    async def soft_delete(self, project_id: uuid.UUID) -> None: ...
    async def has_active_issues(self, project_id: uuid.UUID) -> bool: ...
    async def record_activity(self, entry: ProjectActivityLog) -> ProjectActivityLog: ...


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, project: Project) -> Project:
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.workspace_id == workspace_id,
            Project.deleted_at.is_(None),
        )
        result: Project | None = await self._session.scalar(stmt)
        return result

    async def get_by_slug(self, workspace_id: uuid.UUID, slug: str) -> Project | None:
        stmt = select(Project).where(
            Project.workspace_id == workspace_id,
            Project.slug == slug,
            Project.deleted_at.is_(None),
        )
        result: Project | None = await self._session.scalar(stmt)
        return result

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Project | None:
        """Comparação case-insensitive (`func.lower`) — espelha o índice único
        parcial `uq_projects_workspace_id_name_active` (`lower(name)`), que é
        quem de fato reforça a regra no banco (defesa em profundidade).
        """
        stmt = select(Project).where(
            Project.workspace_id == workspace_id,
            func.lower(Project.name) == name.lower(),
            Project.deleted_at.is_(None),
        )
        result: Project | None = await self._session.scalar(stmt)
        return result

    def _filtered(
        self, workspace_id: uuid.UUID, *, search: str | None, status: ProjectStatus | None
    ) -> Select[tuple[Project]]:
        stmt = select(Project).where(
            Project.workspace_id == workspace_id, Project.deleted_at.is_(None)
        )
        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(Project.status == status)
        return stmt

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        status: ProjectStatus | None = None,
        sort: ProjectSort = "-created_at",
    ) -> Sequence[Project]:
        stmt = (
            self._filtered(workspace_id, search=search, status=status)
            .order_by(_order_by_clause(sort))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        search: str | None = None,
        status: ProjectStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(
            self._filtered(workspace_id, search=search, status=status).subquery()
        )
        return (await self._session.scalar(stmt)) or 0

    async def update(self, project: Project) -> Project:
        """Mesmo racional de `WorkspaceRepository.update`: `project` já é
        rastreado pela sessão (veio de `get_by_id`), então `flush()` já emite o
        `UPDATE` a partir do dirty-tracking do SQLAlchemy — nenhum `UPDATE`
        explícito é necessário aqui.
        """
        await self._session.flush()
        return project

    async def soft_delete(self, project_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Project).where(Project.id == project_id).values(deleted_at=datetime.now(UTC))
        )

    async def has_active_issues(self, project_id: uuid.UUID) -> bool:
        """Espelha a política `ON DELETE RESTRICT` de `issues.project_id` em
        nível de aplicação — necessário porque soft delete não passa pela FK do
        banco (ver `ProjectHasActiveIssuesError`).
        """
        stmt = (
            select(func.count())
            .select_from(_issues_table)
            .where(_issues_table.c.project_id == project_id, _issues_table.c.deleted_at.is_(None))
        )
        count = (await self._session.scalar(stmt)) or 0
        return count > 0

    async def record_activity(self, entry: ProjectActivityLog) -> ProjectActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
