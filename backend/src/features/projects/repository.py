import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.projects.models import Project


class ProjectRepositoryProtocol(Protocol):
    async def create(self, project: Project) -> Project: ...
    async def get_by_id(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Project]: ...


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

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Project]:
        stmt = select(Project).where(
            Project.workspace_id == workspace_id, Project.deleted_at.is_(None)
        )
        return (await self._session.scalars(stmt)).all()
