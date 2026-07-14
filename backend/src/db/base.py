import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid6 import uuid7


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy. Modelos de domínio (Sprint 2+) herdam daqui."""


def domain_enum[EnumT: enum.Enum](enum_cls: type[EnumT], *, length: int = 32) -> SAEnum:
    """VARCHAR + CHECK constraint, nunca ENUM nativo do Postgres — ver docs/03-database.md §5.

    Adicionar um valor é uma migração aditiva simples; alterar um ENUM nativo do
    Postgres historicamente exige cuidado extra (não pode remover valor, ordem importa).
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda cls: [member.value for member in cls],
    )


class UUIDPrimaryKeyMixin:
    """Chave primária UUIDv7, gerada na aplicação — ver docs/03-database.md §1."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)


class TimestampMixin:
    """created_at / updated_at padrão — ver docs/03-database.md §3.

    `eager_defaults=True`: sem isso, `updated_at` (que tem `onupdate` calculado
    pelo servidor) fica marcado como expirado após o `UPDATE` do flush — uma
    leitura subsequente fora de uma coroutine (ex.: `Response.model_validate(obj)`
    logo após `service.update(...)`) tenta um lazy-refresh síncrono e quebra com
    `MissingGreenlet`, já que a engine é assíncrona. Com `eager_defaults=True` e
    Postgres (que suporta `RETURNING`), o valor novo já volta no próprio
    `UPDATE`/`INSERT`, sem round-trip extra nem lazy-load.
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __mapper_args__ = {"eager_defaults": True}


class SoftDeleteMixin:
    """deleted_at nullable — ver docs/03-database.md §2. Repositories filtram por padrão."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
