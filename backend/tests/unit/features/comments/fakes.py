import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.comments.models import Comment, CommentMention
from uuid6 import uuid7


class FakeCommentRepository:
    """Implementa `CommentRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/issues/fakes.py`.
    """

    def __init__(self) -> None:
        self.comments: dict[uuid.UUID, Comment] = {}
        self.mentions: dict[uuid.UUID, list[CommentMention]] = {}

    async def create(self, comment: Comment) -> Comment:
        if comment.id is None:
            comment.id = uuid7()
        now = datetime.now(UTC)
        comment.created_at = comment.created_at or now
        comment.updated_at = comment.updated_at or now
        self.comments[comment.id] = comment
        self.mentions.setdefault(comment.id, [])
        comment.mentions = self.mentions[comment.id]
        return comment

    async def get_by_id(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        comment = self.comments.get(comment_id)
        if (
            comment is None
            or comment.workspace_id != workspace_id
            or comment.deleted_at is not None
        ):
            return None
        return comment

    async def list_by_issue(
        self, issue_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Comment]:
        matches = [
            c for c in self.comments.values() if c.issue_id == issue_id and c.deleted_at is None
        ]
        matches.sort(key=lambda c: c.created_at)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_issue(self, issue_id: uuid.UUID) -> int:
        return len(
            [c for c in self.comments.values() if c.issue_id == issue_id and c.deleted_at is None]
        )

    async def update(self, comment: Comment) -> Comment:
        comment.updated_at = datetime.now(UTC)
        return comment

    async def soft_delete(self, comment_id: uuid.UUID) -> None:
        comment = self.comments.get(comment_id)
        if comment is not None:
            comment.deleted_at = datetime.now(UTC)

    async def add_mentions(self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> None:
        bucket = self.mentions.setdefault(comment_id, [])
        for user_id in user_ids:
            bucket.append(CommentMention(comment_id=comment_id, mentioned_user_id=user_id))

    async def replace_mentions(self, comment_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> None:
        self.mentions[comment_id] = []
        await self.add_mentions(comment_id, user_ids)

    async def refresh_mentions(self, comment: Comment) -> None:
        comment.mentions = self.mentions.get(comment.id, [])
