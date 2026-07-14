import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.labels.models import Label, LabelActivityLog
from uuid6 import uuid7


class FakeLabelRepository:
    """Implementa `LabelRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/projects/fakes.py`.
    """

    def __init__(self) -> None:
        self.labels: dict[uuid.UUID, Label] = {}
        self.activity_log: list[LabelActivityLog] = []

    async def create(self, label: Label) -> Label:
        if label.id is None:
            label.id = uuid7()
        now = datetime.now(UTC)
        label.created_at = label.created_at or now
        label.updated_at = label.updated_at or now
        self.labels[label.id] = label
        return label

    async def get_by_id(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label | None:
        label = self.labels.get(label_id)
        if label is None or label.workspace_id != workspace_id or label.deleted_at is not None:
            return None
        return label

    async def get_by_name(self, workspace_id: uuid.UUID, name: str) -> Label | None:
        for label in self.labels.values():
            if (
                label.workspace_id == workspace_id
                and label.name == name
                and label.deleted_at is None
            ):
                return label
        return None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]:
        matches = [
            label
            for label in self.labels.values()
            if label.workspace_id == workspace_id and label.deleted_at is None
        ]
        matches.sort(key=lambda label: label.name)
        return matches

    async def update(self, label: Label) -> Label:
        label.updated_at = datetime.now(UTC)
        return label

    async def soft_delete(self, label_id: uuid.UUID) -> None:
        label = self.labels.get(label_id)
        if label is not None:
            label.deleted_at = datetime.now(UTC)

    async def record_activity(self, entry: LabelActivityLog) -> LabelActivityLog:
        if entry.id is None:
            entry.id = uuid7()
        entry.created_at = entry.created_at or datetime.now(UTC)
        self.activity_log.append(entry)
        return entry
