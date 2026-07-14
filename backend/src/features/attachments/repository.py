import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.attachments.models import Attachment


class AttachmentRepositoryProtocol(Protocol):
    async def create(self, attachment: Attachment) -> Attachment: ...
    async def get_by_id(
        self, workspace_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> Attachment | None: ...
    async def list_by_issue(self, issue_id: uuid.UUID) -> Sequence[Attachment]: ...
    async def list_by_comment(self, comment_id: uuid.UUID) -> Sequence[Attachment]: ...
    async def soft_delete(self, attachment_id: uuid.UUID) -> None: ...


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, attachment: Attachment) -> Attachment:
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def get_by_id(
        self, workspace_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> Attachment | None:
        stmt = select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.workspace_id == workspace_id,
            Attachment.deleted_at.is_(None),
        )
        result: Attachment | None = await self._session.scalar(stmt)
        return result

    async def list_by_issue(self, issue_id: uuid.UUID) -> Sequence[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.issue_id == issue_id, Attachment.deleted_at.is_(None))
            .order_by(Attachment.created_at.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def list_by_comment(self, comment_id: uuid.UUID) -> Sequence[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.comment_id == comment_id, Attachment.deleted_at.is_(None))
            .order_by(Attachment.created_at.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def soft_delete(self, attachment_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Attachment)
            .where(Attachment.id == attachment_id)
            .values(deleted_at=datetime.now(UTC))
        )
