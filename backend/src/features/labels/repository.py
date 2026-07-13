import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.labels.models import Label


class LabelRepositoryProtocol(Protocol):
    async def create(self, label: Label) -> Label: ...
    async def get_by_id(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]: ...


class LabelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, label: Label) -> Label:
        self._session.add(label)
        await self._session.flush()
        return label

    async def get_by_id(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label | None:
        stmt = select(Label).where(
            Label.id == label_id, Label.workspace_id == workspace_id, Label.deleted_at.is_(None)
        )
        result: Label | None = await self._session.scalar(stmt)
        return result

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]:
        stmt = select(Label).where(Label.workspace_id == workspace_id, Label.deleted_at.is_(None))
        return (await self._session.scalars(stmt)).all()
