import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.labels.models import Label, LabelActivityLog


class LabelRepositoryProtocol(Protocol):
    async def create(self, label: Label) -> Label: ...
    async def get_by_id(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label | None: ...
    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Label | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]: ...
    async def update(self, label: Label) -> Label: ...
    async def soft_delete(self, label_id: uuid.UUID) -> None: ...
    async def record_activity(self, entry: LabelActivityLog) -> LabelActivityLog: ...


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

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Label | None:
        """Comparação exata (não `func.lower`, ao contrário de `Project.name`) —
        espelha o índice único parcial `uq_labels_workspace_id_name_active`, que
        indexa `name` tal como armazenado, não `lower(name)` (`docs/03-database.md` §8).
        """
        stmt = select(Label).where(
            Label.workspace_id == workspace_id, Label.name == name, Label.deleted_at.is_(None)
        )
        result: Label | None = await self._session.scalar(stmt)
        return result

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]:
        stmt = (
            select(Label)
            .where(Label.workspace_id == workspace_id, Label.deleted_at.is_(None))
            .order_by(Label.name.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def update(self, label: Label) -> Label:
        """`label` já é rastreado pela sessão (veio de `get_by_id`) — `flush()`
        já emite o `UPDATE` a partir do dirty-tracking do SQLAlchemy, mesmo
        racional de `ProjectRepository.update`.
        """
        await self._session.flush()
        return label

    async def soft_delete(self, label_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Label).where(Label.id == label_id).values(deleted_at=datetime.now(UTC))
        )

    async def record_activity(self, entry: LabelActivityLog) -> LabelActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
