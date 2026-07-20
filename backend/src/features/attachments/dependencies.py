from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import PermissionService, get_permission_service
from src.core.config import Settings, get_settings
from src.core.db import get_db_session
from src.core.storage import StorageProvider, get_storage_provider
from src.features.attachments.repository import AttachmentRepository, AttachmentRepositoryProtocol
from src.features.attachments.service import AttachmentService
from src.features.issues.repository import IssueRepository, IssueRepositoryProtocol


def get_attachment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AttachmentRepository:
    return AttachmentRepository(session)


def get_attachment_issue_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IssueRepository:
    return IssueRepository(session)


def get_attachment_service(
    attachment_repo: AttachmentRepositoryProtocol = Depends(get_attachment_repository),
    issue_repo: IssueRepositoryProtocol = Depends(get_attachment_issue_repository),
    storage: StorageProvider = Depends(get_storage_provider),
    permission_service: PermissionService = Depends(get_permission_service),
    settings: Settings = Depends(get_settings),
) -> AttachmentService:
    return AttachmentService(
        attachment_repo,
        issue_repo,
        storage,
        permission_service,
        max_size_bytes=settings.max_upload_size_bytes,
        allowed_content_types=settings.allowed_upload_content_types,
    )
