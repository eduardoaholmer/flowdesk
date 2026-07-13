import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.comments.models import Comment


class CommentRepositoryProtocol(Protocol):
    async def create(self, comment: Comment) -> Comment: ...
    async def get_by_id(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None: ...
    async def list_by_issue(self, issue_id: uuid.UUID) -> Sequence[Comment]: ...


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, comment: Comment) -> Comment:
        self._session.add(comment)
        await self._session.flush()
        return comment

    async def get_by_id(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        stmt = select(Comment).where(
            Comment.id == comment_id,
            Comment.workspace_id == workspace_id,
            Comment.deleted_at.is_(None),
        )
        result: Comment | None = await self._session.scalar(stmt)
        return result

    async def list_by_issue(self, issue_id: uuid.UUID) -> Sequence[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.issue_id == issue_id, Comment.deleted_at.is_(None))
            .order_by(Comment.created_at)
        )
        return (await self._session.scalars(stmt)).all()
