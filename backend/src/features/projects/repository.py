import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from sqlalchemy import Select, column, delete, func, select, table, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.features.projects.models import (
    Project,
    ProjectActivityLog,
    ProjectMember,
    ProjectStatus,
)

# Referência Core (não ORM) à tabela `issues` — só o suficiente para as
# checagens/agregações deste repositório (`has_active_issues`, `issue_counts`).
# Importar o model `Issue` aqui obrigaria o SQLAlchemy a configurar o mapper
# inteiro de `Issue` (incluindo seu relationship com `Comment`) assim que
# `ProjectRepository` fosse carregado — acoplando Projects ao grafo de mappers
# de uma feature (Issues/Comments). `sqlalchemy.table()`/`column()` consultam
# por nome de coluna sem passar pelo registry declarativo, evitando isso.
_issues_table = table("issues", column("project_id"), column("deleted_at"), column("status"))

# Espelha `IssueStatus.DONE` sem importar `features/issues/models` (mesmo
# racional de `_issues_table`): só o valor da string entra na agregação de
# progresso, não o enum nem o mapper de `Issue`.
_DONE_STATUS = "DONE"

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
    async def get_by_key(self, workspace_id: uuid.UUID, key: str) -> Project | None: ...
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
    async def add_member(self, member: ProjectMember) -> bool: ...
    async def remove_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool: ...
    async def list_member_ids(
        self, project_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, list[uuid.UUID]]: ...
    async def issue_counts(
        self, project_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int]]: ...
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

    async def get_by_key(self, workspace_id: uuid.UUID, key: str) -> Project | None:
        stmt = select(Project).where(
            Project.workspace_id == workspace_id,
            Project.key == key,
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

    async def add_member(self, member: ProjectMember) -> bool:
        """Idempotente: adicionar um usuário já vinculado é no-op (não erro).
        `ON CONFLICT DO NOTHING` + `RETURNING id` distingue inserção real de
        conflito numa única query — o `id` só volta quando a linha foi de fato
        criada, o que o service usa para registrar (ou não) a atividade.
        """
        stmt = (
            pg_insert(ProjectMember)
            .values(
                id=uuid7(),
                workspace_id=member.workspace_id,
                project_id=member.project_id,
                user_id=member.user_id,
            )
            .on_conflict_do_nothing(
                index_elements=[ProjectMember.project_id, ProjectMember.user_id]
            )
            .returning(ProjectMember.id)
        )
        inserted = await self._session.scalar(stmt)
        return inserted is not None

    async def remove_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = (
            delete(ProjectMember)
            .where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            .returning(ProjectMember.id)
        )
        removed = await self._session.scalar(stmt)
        return removed is not None

    async def list_member_ids(
        self, project_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, list[uuid.UUID]]:
        """Uma query para uma página inteira de projetos (evita N+1). Devolve
        um dict já com chave para cada `project_id` pedido, mesmo os sem membro.
        """
        members: dict[uuid.UUID, list[uuid.UUID]] = {pid: [] for pid in project_ids}
        if not project_ids:
            return members
        stmt = (
            select(ProjectMember.project_id, ProjectMember.user_id)
            .where(ProjectMember.project_id.in_(project_ids))
            .order_by(ProjectMember.created_at.asc())
        )
        for project_id, user_id in (await self._session.execute(stmt)).all():
            members[project_id].append(user_id)
        return members

    async def issue_counts(
        self, project_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int]]:
        """Uma agregação (`GROUP BY project_id`) para uma página inteira — total
        de issues não deletadas e quantas em `DONE`, suficiente para a barra de
        progresso "concluídas/total" do frontend. Nunca uma query por projeto.
        """
        counts: dict[uuid.UUID, tuple[int, int]] = {pid: (0, 0) for pid in project_ids}
        if not project_ids:
            return counts
        stmt = (
            select(
                _issues_table.c.project_id,
                func.count().label("total"),
                func.count().filter(_issues_table.c.status == _DONE_STATUS).label("done"),
            )
            .where(
                _issues_table.c.project_id.in_(project_ids),
                _issues_table.c.deleted_at.is_(None),
            )
            .group_by(_issues_table.c.project_id)
        )
        for project_id, total, done in (await self._session.execute(stmt)).all():
            counts[project_id] = (total, done)
        return counts

    async def record_activity(self, entry: ProjectActivityLog) -> ProjectActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
