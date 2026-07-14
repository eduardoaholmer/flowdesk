from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import PermissionService, get_permission_service
from src.core.db import get_db_session
from src.features.comments.repository import CommentRepository, CommentRepositoryProtocol
from src.features.comments.service import CommentService
from src.features.issues.repository import IssueRepository, IssueRepositoryProtocol
from src.features.workspaces.repository import WorkspaceRepository, WorkspaceRepositoryProtocol


def get_comment_repository(session: AsyncSession = Depends(get_db_session)) -> CommentRepository:
    return CommentRepository(session)


def get_comment_issue_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IssueRepository:
    return IssueRepository(session)


def get_comment_workspace_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def get_comment_service(
    comment_repo: CommentRepositoryProtocol = Depends(get_comment_repository),
    issue_repo: IssueRepositoryProtocol = Depends(get_comment_issue_repository),
    workspace_repo: WorkspaceRepositoryProtocol = Depends(get_comment_workspace_repository),
    permission_service: PermissionService = Depends(get_permission_service),
) -> CommentService:
    return CommentService(comment_repo, issue_repo, workspace_repo, permission_service)
