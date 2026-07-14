import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.projects.models import Project, ProjectActivityLog, ProjectStatus
from src.features.projects.repository import ProjectSort
from uuid6 import uuid7


class FakeProjectRepository:
    """Implementa `ProjectRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/workspaces/fakes.py`: testar o
    service sem banco, simulando os defaults que só existem no flush do
    SQLAlchemy real.
    """

    def __init__(self) -> None:
        self.projects: dict[uuid.UUID, Project] = {}
        self.activity_log: list[ProjectActivityLog] = []
        # Controlado diretamente pelo teste — simula issues ativas vinculadas a
        # um projeto sem precisar de um `IssueRepository` real (a feature de
        # Issues ainda não existe nesta sprint, ver `ProjectHasActiveIssuesError`).
        self.projects_with_active_issues: set[uuid.UUID] = set()

    async def create(self, project: Project) -> Project:
        if project.id is None:
            project.id = uuid7()
        now = datetime.now(UTC)
        project.created_at = project.created_at or now
        project.updated_at = project.updated_at or now
        self.projects[project.id] = project
        return project

    async def get_by_id(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project | None:
        project = self.projects.get(project_id)
        if (
            project is None
            or project.workspace_id != workspace_id
            or project.deleted_at is not None
        ):
            return None
        return project

    async def get_by_slug(self, workspace_id: uuid.UUID, slug: str) -> Project | None:
        for project in self.projects.values():
            if (
                project.workspace_id == workspace_id
                and project.slug == slug
                and project.deleted_at is None
            ):
                return project
        return None

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Project | None:
        for project in self.projects.values():
            if (
                project.workspace_id == workspace_id
                and project.name.lower() == name.lower()
                and project.deleted_at is None
            ):
                return project
        return None

    def _filtered(
        self, workspace_id: uuid.UUID, *, search: str | None, status: ProjectStatus | None
    ) -> list[Project]:
        matches = [
            p
            for p in self.projects.values()
            if p.workspace_id == workspace_id and p.deleted_at is None
        ]
        if search:
            matches = [p for p in matches if search.lower() in p.name.lower()]
        if status is not None:
            matches = [p for p in matches if p.status == status]
        return matches

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
        matches = self._filtered(workspace_id, search=search, status=status)
        field = sort[1:] if sort.startswith("-") else sort
        reverse = sort.startswith("-")
        matches.sort(key=lambda p: getattr(p, field) or "", reverse=reverse)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        search: str | None = None,
        status: ProjectStatus | None = None,
    ) -> int:
        return len(self._filtered(workspace_id, search=search, status=status))

    async def update(self, project: Project) -> Project:
        project.updated_at = datetime.now(UTC)
        return project

    async def soft_delete(self, project_id: uuid.UUID) -> None:
        project = self.projects.get(project_id)
        if project is not None:
            project.deleted_at = datetime.now(UTC)

    async def has_active_issues(self, project_id: uuid.UUID) -> bool:
        return project_id in self.projects_with_active_issues

    async def record_activity(self, entry: ProjectActivityLog) -> ProjectActivityLog:
        if entry.id is None:
            entry.id = uuid7()
        entry.created_at = entry.created_at or datetime.now(UTC)
        self.activity_log.append(entry)
        return entry
