import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import column, func, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.labels.models import Label, LabelActivityLog

# Referências Core (não ORM) às tabelas do domínio de Issues — só o suficiente
# para a agregação de uso (`issue_counts`), sem importar `features/issues/models`
# e arrastar o mapper de `Issue` para dentro de Labels (mesmo racional de
# `ProjectRepository._issues_table`).
_issue_labels_table = table("issue_labels", column("issue_id"), column("label_id"))
_issues_table = table("issues", column("id"), column("deleted_at"))


class LabelRepositoryProtocol(Protocol):
    async def create(self, label: Label) -> Label: ...
    async def get_by_id(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label | None: ...
    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Label | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]: ...
    async def update(self, label: Label) -> Label: ...
    async def soft_delete(self, label_id: uuid.UUID) -> None: ...
    async def issue_counts(self, label_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]: ...
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

    async def issue_counts(self, label_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Uma agregação para uma página inteira de labels (evita N+1): conta as
        issues não deletadas que carregam cada label, via a tabela de junção
        `issue_labels`. Devolve 0 para labels sem nenhuma issue.
        """
        counts: dict[uuid.UUID, int] = {label_id: 0 for label_id in label_ids}
        if not label_ids:
            return counts
        stmt = (
            select(_issue_labels_table.c.label_id, func.count())
            .select_from(
                _issue_labels_table.join(
                    _issues_table, _issues_table.c.id == _issue_labels_table.c.issue_id
                )
            )
            .where(
                _issue_labels_table.c.label_id.in_(label_ids),
                _issues_table.c.deleted_at.is_(None),
            )
            .group_by(_issue_labels_table.c.label_id)
        )
        for label_id, count in (await self._session.execute(stmt)).all():
            counts[label_id] = count
        return counts

    async def record_activity(self, entry: LabelActivityLog) -> LabelActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
