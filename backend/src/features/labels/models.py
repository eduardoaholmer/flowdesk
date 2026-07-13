import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.features.issues.models import IssueLabel


class Label(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "labels"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    color: Mapped[str] = mapped_column(nullable=False)

    issue_links: Mapped[list["IssueLabel"]] = relationship(
        back_populates="label", passive_deletes=True
    )


Index(
    "uq_labels_workspace_id_name_active",
    Label.workspace_id,
    Label.name,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
