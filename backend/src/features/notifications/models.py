import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, UUIDPrimaryKeyMixin, domain_enum
from src.features.auth.models import User


class NotificationType(enum.StrEnum):
    MENTION = "MENTION"
    ASSIGNMENT = "ASSIGNMENT"
    STATUS_CHANGE = "STATUS_CHANGE"


class Notification(UUIDPrimaryKeyMixin, Base):
    """Descartável (delete físico ou expiração), sem valor histórico que justifique
    soft delete — docs/03-database.md §2.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_read_at_created_at", "user_id", "read_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(domain_enum(NotificationType), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
