from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.features.labels.repository import LabelRepository, LabelRepositoryProtocol
from src.features.labels.service import LabelService


def get_label_repository(session: AsyncSession = Depends(get_db_session)) -> LabelRepository:
    return LabelRepository(session)


def get_label_service(
    label_repo: LabelRepositoryProtocol = Depends(get_label_repository),
) -> LabelService:
    return LabelService(label_repo)
