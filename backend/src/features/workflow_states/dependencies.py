from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.features.workflow_states.repository import (
    WorkflowStateRepository,
    WorkflowStateRepositoryProtocol,
)
from src.features.workflow_states.service import WorkflowStateService


def get_workflow_state_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowStateRepository:
    return WorkflowStateRepository(session)


def get_workflow_state_service(
    workflow_state_repo: WorkflowStateRepositoryProtocol = Depends(get_workflow_state_repository),
) -> WorkflowStateService:
    return WorkflowStateService(workflow_state_repo)
