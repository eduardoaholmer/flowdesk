from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataEnvelope(BaseModel, Generic[T]):
    """Envelope de sucesso padrão (CLAUDE.md §8) — `{"data": ...}`.

    Toda rota usa isso (ou um envelope de coleção com `meta`, quando essa
    primeira feature de paginação existir) como `response_model`, nunca
    retornando o schema de recurso "nu".
    """

    data: T
