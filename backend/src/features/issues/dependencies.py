from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import PermissionService, get_permission_service
from src.core.db import get_db_session
from src.features.issues.repository import IssueRepository, IssueRepositoryProtocol
from src.features.issues.service import IssueService
from src.features.labels.repository import LabelRepository, LabelRepositoryProtocol
from src.features.notifications.dependencies import get_notification_service
from src.features.notifications.service import NotificationService
from src.features.projects.repository import ProjectRepository, ProjectRepositoryProtocol
from src.features.workflow_states.repository import (
    WorkflowStateRepository,
    WorkflowStateRepositoryProtocol,
)


def get_issue_repository(session: AsyncSession = Depends(get_db_session)) -> IssueRepository:
    return IssueRepository(session)


def get_issue_project_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRepository:
    return ProjectRepository(session)


def get_issue_label_repository(
    session: AsyncSession = Depends(get_db_session),
) -> LabelRepository:
    return LabelRepository(session)


def get_issue_workflow_state_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowStateRepository:
    return WorkflowStateRepository(session)


def get_issue_service(
    issue_repo: IssueRepositoryProtocol = Depends(get_issue_repository),
    permission_service: PermissionService = Depends(get_permission_service),
    project_repo: ProjectRepositoryProtocol = Depends(get_issue_project_repository),
    label_repo: LabelRepositoryProtocol = Depends(get_issue_label_repository),
    notification_service: NotificationService = Depends(get_notification_service),
    workflow_state_repo: WorkflowStateRepositoryProtocol = Depends(
        get_issue_workflow_state_repository
    ),
) -> IssueService:
    return IssueService(
        issue_repo,
        permission_service,
        project_repo,
        label_repo,
        notification_service,
        workflow_state_repo,
    )
