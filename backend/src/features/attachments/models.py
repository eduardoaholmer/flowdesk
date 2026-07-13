import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from src.features.auth.models import User
from src.features.comments.models import Comment
from src.features.issues.models import Issue


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Associação polimórfica simples com issue OU comment (nunca os dois, nunca
    nenhum) — `issue_id`/`comment_id` nullable + CHECK garantindo exatamente um.
    `storage_key` é um ponteiro opaco para o blob storage real (S3 ou equivalente);
    o backend de armazenamento em si fica fora de escopo desta sprint.
    """

    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(issue_id, comment_id) = 1",
            name="ck_attachments_exactly_one_parent",
        ),
        Index("ix_attachments_issue_id", "issue_id"),
        Index("ix_attachments_comment_id", "comment_id"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("issues.id", ondelete="RESTRICT"), default=None
    )
    comment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="RESTRICT"), default=None
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(nullable=False)

    issue: Mapped[Issue | None] = relationship()
    comment: Mapped[Comment | None] = relationship(back_populates="attachments")
    uploader: Mapped[User] = relationship()
