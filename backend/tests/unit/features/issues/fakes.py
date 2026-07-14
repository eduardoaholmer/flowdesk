import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.issues.models import ActivityLog, Issue, IssueLabel, IssuePriority
from src.features.issues.repository import IssueSort
from uuid6 import uuid7

_PRIORITY_RANK = {
    IssuePriority.NO_PRIORITY: 0,
    IssuePriority.LOW: 1,
    IssuePriority.MEDIUM: 2,
    IssuePriority.HIGH: 3,
    IssuePriority.URGENT: 4,
}


class FakeIssueRepository:
    """Implementa `IssueRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/projects/fakes.py`.
    """

    def __init__(self) -> None:
        self.issues: dict[uuid.UUID, Issue] = {}
        self.activity_log: list[ActivityLog] = []
        self.labels: list[IssueLabel] = []
        self._next_number: dict[uuid.UUID, int] = {}

    async def create(self, issue: Issue) -> Issue:
        """Replica os defaults que só existem no flush do SQLAlchemy real
        (`version` tem `default=1` a nível de coluna, nunca aplicado ao
        simplesmente instanciar `Issue(...)` sem passar pela sessão).
        """
        if issue.id is None:
            issue.id = uuid7()
        now = datetime.now(UTC)
        issue.created_at = issue.created_at or now
        issue.updated_at = issue.updated_at or now
        if issue.version is None:
            issue.version = 1
        self.issues[issue.id] = issue
        return issue

    async def get_by_id(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue | None:
        issue = self.issues.get(issue_id)
        if issue is None or issue.workspace_id != workspace_id or issue.deleted_at is not None:
            return None
        return issue

    async def next_number(self, workspace_id: uuid.UUID) -> int:
        current = self._next_number.get(workspace_id, 1)
        self._next_number[workspace_id] = current + 1
        return current

    def _filtered(
        self,
        workspace_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None,
        status: object | None,
        priority: object | None,
        assignee_id: uuid.UUID | None,
        creator_id: uuid.UUID | None,
        search: str | None,
    ) -> list[Issue]:
        matches = [
            i
            for i in self.issues.values()
            if i.workspace_id == workspace_id and i.deleted_at is None
        ]
        if project_id is not None:
            matches = [i for i in matches if i.project_id == project_id]
        if status is not None:
            matches = [i for i in matches if i.status == status]
        if priority is not None:
            matches = [i for i in matches if i.priority == priority]
        if assignee_id is not None:
            matches = [i for i in matches if i.assignee_id == assignee_id]
        if creator_id is not None:
            matches = [i for i in matches if i.creator_id == creator_id]
        if search:
            lowered = search.lower()
            matches = [
                i
                for i in matches
                if lowered in i.title.lower()
                or (i.description is not None and lowered in i.description.lower())
                or lowered in i.identifier.lower()
            ]
        return matches

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        project_id: uuid.UUID | None = None,
        status: object | None = None,
        priority: object | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
        sort: IssueSort = "-updated_at",
    ) -> Sequence[Issue]:
        matches = self._filtered(
            workspace_id,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            creator_id=creator_id,
            search=search,
        )
        field = sort[1:] if sort.startswith("-") else sort
        reverse = sort.startswith("-")
        if field == "priority":
            matches.sort(key=lambda i: _PRIORITY_RANK[i.priority], reverse=reverse)
        else:
            matches.sort(key=lambda i: getattr(i, field) or 0, reverse=reverse)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        status: object | None = None,
        priority: object | None = None,
        assignee_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> int:
        return len(
            self._filtered(
                workspace_id,
                project_id=project_id,
                status=status,
                priority=priority,
                assignee_id=assignee_id,
                creator_id=creator_id,
                search=search,
            )
        )

    async def update(self, issue: Issue) -> Issue:
        issue.updated_at = datetime.now(UTC)
        return issue

    async def soft_delete(self, issue_id: uuid.UUID) -> None:
        issue = self.issues.get(issue_id)
        if issue is not None:
            issue.deleted_at = datetime.now(UTC)

    async def add_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel:
        link = IssueLabel(issue_id=issue_id, label_id=label_id)
        self.labels.append(link)
        return link

    async def remove_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None:
        self.labels = [
            link
            for link in self.labels
            if not (link.issue_id == issue_id and link.label_id == label_id)
        ]

    async def get_label_link(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel | None:
        for link in self.labels:
            if link.issue_id == issue_id and link.label_id == label_id:
                return link
        return None

    async def list_labels(self, issue_id: uuid.UUID) -> Sequence[object]:
        """Retorna só os vínculos (`IssueLabel`), não os `Label` completos —
        suficiente para os testes de serviço que hoje exercitam esta fake
        (que verificam contagem/ids de vínculo, não os campos do Label em si).
        """
        return [link for link in self.labels if link.issue_id == issue_id]

    async def record_activity(self, entry: ActivityLog) -> ActivityLog:
        if entry.id is None:
            entry.id = uuid7()
        entry.created_at = entry.created_at or datetime.now(UTC)
        self.activity_log.append(entry)
        return entry

    async def list_activity(self, issue_id: uuid.UUID) -> Sequence[ActivityLog]:
        return [entry for entry in self.activity_log if entry.issue_id == issue_id]
