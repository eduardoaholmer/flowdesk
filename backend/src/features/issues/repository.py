import re
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from sqlalchemy import ColumnElement, Select, case, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.issues.models import (
    ActivityLog,
    Issue,
    IssueLabel,
    IssuePriority,
    IssueStatus,
    WorkspaceIssueCounter,
)
from src.features.labels.models import Label

# Reconhece busca por identificador ("FD-123", "fd-123") ou número puro ("123"),
# além da busca textual full-text sobre título/descrição — RF de busca desta
# sprint pede título, descrição *e* identificador (CLAUDE.md, seção "Busca").
_IDENTIFIER_SEARCH_RE = re.compile(r"^(?:fd-)?(\d+)$", re.IGNORECASE)

IssueSort = Literal[
    "number",
    "-number",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "priority",
    "-priority",
    "due_date",
    "-due_date",
]

_PRIORITY_RANK = case(
    (Issue.priority == IssuePriority.NO_PRIORITY, 0),
    (Issue.priority == IssuePriority.LOW, 1),
    (Issue.priority == IssuePriority.MEDIUM, 2),
    (Issue.priority == IssuePriority.HIGH, 3),
    (Issue.priority == IssuePriority.URGENT, 4),
)

_SORT_COLUMNS: dict[str, Any] = {
    "number": Issue.number,
    "created_at": Issue.created_at,
    "updated_at": Issue.updated_at,
    "priority": _PRIORITY_RANK,
    "due_date": Issue.due_date,
}


def _order_by_clause(sort: IssueSort) -> Any:
    field = sort[1:] if sort.startswith("-") else sort
    column = _SORT_COLUMNS[field]
    return column.desc() if sort.startswith("-") else column.asc()


class IssueRepositoryProtocol(Protocol):
    async def create(self, issue: Issue) -> Issue: ...
    async def get_by_id(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue | None: ...
    async def next_number(self, workspace_id: uuid.UUID) -> int: ...
    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        project_id: uuid.UUID | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
        sort: IssueSort = "-updated_at",
    ) -> Sequence[Issue]: ...
    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> int: ...
    async def update(self, issue: Issue) -> Issue: ...
    async def soft_delete(self, issue_id: uuid.UUID) -> None: ...
    async def add_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel: ...
    async def remove_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None: ...
    async def get_label_link(
        self, issue_id: uuid.UUID, label_id: uuid.UUID
    ) -> IssueLabel | None: ...
    async def list_labels(self, issue_id: uuid.UUID) -> Sequence[Label]: ...
    async def record_activity(self, entry: ActivityLog) -> ActivityLog: ...
    async def list_activity(self, issue_id: uuid.UUID) -> Sequence[ActivityLog]: ...


class IssueRepository:
    """Também guarda-chuva de `IssueLabel` (associação N:N) e `ActivityLog`
    (append-only) — ambos são filhos do agregado Issue, não agregados próprios.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, issue: Issue) -> Issue:
        self._session.add(issue)
        await self._session.flush()
        return issue

    async def get_by_id(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue | None:
        stmt = select(Issue).where(
            Issue.id == issue_id,
            Issue.workspace_id == workspace_id,
            Issue.deleted_at.is_(None),
        )
        result: Issue | None = await self._session.scalar(stmt)
        return result

    async def next_number(self, workspace_id: uuid.UUID) -> int:
        """Gera o próximo `number` sequencial do workspace de forma atômica.

        `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` cria a linha do
        contador sob demanda na primeira issue do workspace e a incrementa nas
        seguintes — sem depender de uma linha pré-criada por um evento de
        criação de workspace (ver ADR-012, Decisão 3, docs/09-decision-log.md).
        """
        stmt = (
            pg_insert(WorkspaceIssueCounter)
            .values(workspace_id=workspace_id, next_number=2)
            .on_conflict_do_update(
                index_elements=[WorkspaceIssueCounter.workspace_id],
                set_={"next_number": WorkspaceIssueCounter.next_number + 1},
            )
            .returning(WorkspaceIssueCounter.next_number)
        )
        result = await self._session.execute(stmt)
        issued_plus_one: int = result.scalar_one()
        return issued_plus_one - 1

    def _filtered(
        self,
        workspace_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None,
        status: IssueStatus | None,
        priority: IssuePriority | None,
        assignee_id: uuid.UUID | None,
        creator_id: uuid.UUID | None,
        search: str | None,
    ) -> Select[tuple[Issue]]:
        stmt = select(Issue).where(Issue.workspace_id == workspace_id, Issue.deleted_at.is_(None))
        if project_id is not None:
            stmt = stmt.where(Issue.project_id == project_id)
        if status is not None:
            stmt = stmt.where(Issue.status == status)
        if priority is not None:
            stmt = stmt.where(Issue.priority == priority)
        if assignee_id is not None:
            stmt = stmt.where(Issue.assignee_id == assignee_id)
        if creator_id is not None:
            stmt = stmt.where(Issue.creator_id == creator_id)
        if search:
            conditions: list[ColumnElement[bool]] = [
                func.to_tsvector(
                    "simple", Issue.title + " " + func.coalesce(Issue.description, "")
                ).op("@@")(func.plainto_tsquery("simple", search))
            ]
            identifier_match = _IDENTIFIER_SEARCH_RE.match(search.strip())
            if identifier_match:
                conditions.append(Issue.number == int(identifier_match.group(1)))
            stmt = stmt.where(or_(*conditions))
        return stmt

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        project_id: uuid.UUID | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
        sort: IssueSort = "-updated_at",
    ) -> Sequence[Issue]:
        stmt = (
            self._filtered(
                workspace_id,
                project_id=project_id,
                status=status,
                priority=priority,
                assignee_id=assignee_id,
                creator_id=creator_id,
                search=search,
            )
            .order_by(_order_by_clause(sort))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(
            self._filtered(
                workspace_id,
                project_id=project_id,
                status=status,
                priority=priority,
                assignee_id=assignee_id,
                creator_id=creator_id,
                search=search,
            ).subquery()
        )
        return (await self._session.scalar(stmt)) or 0

    async def update(self, issue: Issue) -> Issue:
        """`issue` já é rastreado pela sessão (veio de `get_by_id`), então
        `flush()` já emite o `UPDATE` a partir do dirty-tracking do SQLAlchemy
        (mesmo racional de `ProjectRepository.update`) — a checagem de
        concorrência otimista (versão esperada == `issue.version`) acontece no
        service, antes de mutar o objeto, não aqui.
        """
        await self._session.flush()
        return issue

    async def soft_delete(self, issue_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Issue).where(Issue.id == issue_id).values(deleted_at=datetime.now(UTC))
        )

    async def add_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel:
        link = IssueLabel(issue_id=issue_id, label_id=label_id)
        self._session.add(link)
        await self._session.flush()
        return link

    async def remove_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None:
        stmt = delete(IssueLabel).where(
            IssueLabel.issue_id == issue_id, IssueLabel.label_id == label_id
        )
        await self._session.execute(stmt)

    async def get_label_link(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel | None:
        stmt = select(IssueLabel).where(
            IssueLabel.issue_id == issue_id, IssueLabel.label_id == label_id
        )
        result: IssueLabel | None = await self._session.scalar(stmt)
        return result

    async def list_labels(self, issue_id: uuid.UUID) -> Sequence[Label]:
        stmt = (
            select(Label)
            .join(IssueLabel, IssueLabel.label_id == Label.id)
            .where(IssueLabel.issue_id == issue_id, Label.deleted_at.is_(None))
            .order_by(Label.name.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def record_activity(self, entry: ActivityLog) -> ActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_activity(self, issue_id: uuid.UUID) -> Sequence[ActivityLog]:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.issue_id == issue_id)
            .order_by(ActivityLog.created_at.desc())
        )
        return (await self._session.scalars(stmt)).all()
