from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.features.permissions.repository import (
    PermissionOverrideRepository,
    PermissionOverrideRepositoryProtocol,
)
from src.features.permissions.service import PermissionOverrideService


def get_permission_override_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PermissionOverrideRepository:
    return PermissionOverrideRepository(session)


def get_permission_override_service(
    repo: PermissionOverrideRepositoryProtocol = Depends(get_permission_override_repository),
) -> PermissionOverrideService:
    return PermissionOverrideService(repo)
