import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.issues.models import ActivityLog, Issue, IssueLabel


class IssueRepositoryProtocol(Protocol):
    async def create(self, issue: Issue) -> Issue: ...
    async def get_by_id(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue | None: ...
    async def list_by_team_and_status(
        self, workspace_id: uuid.UUID, team_id: uuid.UUID, status_id: uuid.UUID
    ) -> Sequence[Issue]: ...
    async def add_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel: ...
    async def remove_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None: ...
    async def record_activity(self, entry: ActivityLog) -> ActivityLog: ...


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

    async def list_by_team_and_status(
        self, workspace_id: uuid.UUID, team_id: uuid.UUID, status_id: uuid.UUID
    ) -> Sequence[Issue]:
        stmt = select(Issue).where(
            Issue.workspace_id == workspace_id,
            Issue.team_id == team_id,
            Issue.status_id == status_id,
            Issue.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).all()

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

    async def record_activity(self, entry: ActivityLog) -> ActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
