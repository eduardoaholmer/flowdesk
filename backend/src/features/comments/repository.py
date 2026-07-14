import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.features.comments.models import Comment, CommentMention


class CommentRepositoryProtocol(Protocol):
    async def create(self, comment: Comment) -> Comment: ...
    async def get_by_id(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None: ...
    async def list_by_issue(
        self, issue_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Comment]: ...
    async def count_by_issue(self, issue_id: uuid.UUID) -> int: ...
    async def update(self, comment: Comment) -> Comment: ...
    async def soft_delete(self, comment_id: uuid.UUID) -> None: ...
    async def add_mentions(self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> None: ...
    async def replace_mentions(
        self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]
    ) -> None: ...
    async def refresh_mentions(self, comment: Comment) -> None: ...


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, comment: Comment) -> Comment:
        self._session.add(comment)
        await self._session.flush()
        return comment

    async def get_by_id(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        stmt = (
            select(Comment)
            .where(
                Comment.id == comment_id,
                Comment.workspace_id == workspace_id,
                Comment.deleted_at.is_(None),
            )
            .options(selectinload(Comment.mentions))
        )
        result: Comment | None = await self._session.scalar(stmt)
        return result

    async def list_by_issue(
        self, issue_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Comment]:
        """`selectinload(Comment.mentions)` evita N+1 ao serializar
        `CommentResponse.mentioned_user_ids` para toda a página de uma vez
        (uma segunda query batched, não uma por comentário — CLAUDE.md, seção
        "Performance").
        """
        stmt = (
            select(Comment)
            .where(Comment.issue_id == issue_id, Comment.deleted_at.is_(None))
            .options(selectinload(Comment.mentions))
            .order_by(Comment.created_at.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_issue(self, issue_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Comment)
            .where(Comment.issue_id == issue_id, Comment.deleted_at.is_(None))
        )
        return (await self._session.scalar(stmt)) or 0

    async def update(self, comment: Comment) -> Comment:
        await self._session.flush()
        return comment

    async def soft_delete(self, comment_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Comment).where(Comment.id == comment_id).values(deleted_at=datetime.now(UTC))
        )

    async def add_mentions(self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> None:
        for user_id in user_ids:
            self._session.add(CommentMention(comment_id=comment_id, mentioned_user_id=user_id))
        if user_ids:
            await self._session.flush()

    async def replace_mentions(self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> None:
        """Usado por `CommentService.update`: em vez de calcular um diff
        adicionar/remover, apaga todas as menções antigas e reinsere o
        conjunto atual — o volume por comentário é pequeno o suficiente
        (poucas menções) para que a simplicidade valha mais que a economia de
        um `DELETE` a mais (`CLAUDE.md` §1.1).
        """
        await self._session.execute(
            delete(CommentMention).where(CommentMention.comment_id == comment_id)
        )
        await self.add_mentions(comment_id, user_ids)

    async def refresh_mentions(self, comment: Comment) -> None:
        """`add_mentions`/`replace_mentions` inserem `CommentMention` via FK
        direto (`comment_id=...`), não via `comment.mentions.append(...)` — o
        relationship em memória de `comment` fica desatualizado até um refresh
        explícito. `AsyncSession.refresh(attribute_names=...)` é a forma
        async-safe de recarregar só essa coleção (um lazy-load de atributo
        comum, fora deste método, quebraria com `MissingGreenlet` sob engine
        assíncrona).
        """
        await self._session.refresh(comment, attribute_names=["mentions"])
