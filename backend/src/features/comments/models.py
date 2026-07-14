import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from src.features.auth.models import User
from src.features.issues.models import Issue

if TYPE_CHECKING:
    from src.features.attachments.models import Attachment


class Comment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_issue_id_deleted_at_created_at", "issue_id", "deleted_at", "created_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    body: Mapped[str] = mapped_column(nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="comment")
    mentions: Mapped[list["CommentMention"]] = relationship(
        back_populates="comment", passive_deletes=True
    )

    @property
    def mentioned_user_ids(self) -> list[uuid.UUID]:
        """Deriva da relationship `mentions`, sempre eager-loaded pelo
        repository (`selectinload`) — nunca lazy-load em contexto async
        (`CLAUDE.md` §3, comportamento trivial derivado de dado).
        """
        return [mention.mentioned_user_id for mention in self.mentions]


class CommentMention(Base):
    """Relação pura N:N entre `Comment` e o `User` mencionado (`@usuario` no
    corpo do comentário) — mesmo padrão de `IssueLabel`
    (`features/issues/models.py`): classe explícita em vez de `Table` solta,
    para deixar espaço a metadado futuro (ex.: `notified_at`, quando a Sprint
    de notificações em tempo real consumir esta tabela) sem exigir converter
    uma Table em entidade depois.

    Detecção/validação/armazenamento são o escopo desta sprint (`CLAUDE.md`,
    "Menções") — nenhum envio de notificação ainda; ver `CommentService._extract_mentions`.
    """

    __tablename__ = "comment_mentions"

    comment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True
    )
    mentioned_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    comment: Mapped[Comment] = relationship(back_populates="mentions")
    mentioned_user: Mapped[User] = relationship()
