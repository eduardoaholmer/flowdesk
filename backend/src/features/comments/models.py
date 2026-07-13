import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
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
