import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid6 import uuid7


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy. Modelos de domínio (Sprint 2+) herdam daqui."""


class UUIDPrimaryKeyMixin:
    """Chave primária UUIDv7, gerada na aplicação — ver docs/03-database.md §1."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)


class TimestampMixin:
    """created_at / updated_at padrão — ver docs/03-database.md §3."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """deleted_at nullable — ver docs/03-database.md §2. Repositories filtram por padrão."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
