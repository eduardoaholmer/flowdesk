from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.features.projects.repository import ProjectRepository, ProjectRepositoryProtocol
from src.features.projects.service import ProjectService


def get_project_repository(session: AsyncSession = Depends(get_db_session)) -> ProjectRepository:
    return ProjectRepository(session)


def get_project_service(
    project_repo: ProjectRepositoryProtocol = Depends(get_project_repository),
) -> ProjectService:
    return ProjectService(project_repo)
