import math
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataEnvelope(BaseModel, Generic[T]):
    """Envelope de sucesso padrão (CLAUDE.md §8) — `{"data": ...}`.

    Toda rota de recurso único usa isso como `response_model`, nunca retornando
    o schema de recurso "nu". Coleções paginadas usam `CollectionEnvelope` abaixo.
    """

    data: T


class PaginationMeta(BaseModel):
    """`meta` de uma coleção paginada por offset (CLAUDE.md §8) — usada pelas
    coleções pequenas e estáveis descritas em `docs/04-api-design.md` §1
    (workspaces, members), nunca pelas de alto volume (cursor-based).
    """

    page: int
    per_page: int
    total: int
    total_pages: int

    @classmethod
    def build(cls, *, page: int, per_page: int, total: int) -> "PaginationMeta":
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        return cls(page=page, per_page=per_page, total=total, total_pages=total_pages)


class CollectionEnvelope(BaseModel, Generic[T]):
    """Envelope de sucesso padrão para coleção paginada — `{"data": [...], "meta": {...}}`."""

    data: list[T]
    meta: PaginationMeta
