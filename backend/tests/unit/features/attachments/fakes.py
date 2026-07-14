import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import BinaryIO

from src.features.attachments.models import Attachment
from uuid6 import uuid7


class FakeAttachmentRepository:
    """Implementa `AttachmentRepositoryProtocol` em memória (`CLAUDE.md` §5/§6)."""

    def __init__(self) -> None:
        self.attachments: dict[uuid.UUID, Attachment] = {}

    async def create(self, attachment: Attachment) -> Attachment:
        if attachment.id is None:
            attachment.id = uuid7()
        now = datetime.now(UTC)
        attachment.created_at = attachment.created_at or now
        attachment.updated_at = attachment.updated_at or now
        self.attachments[attachment.id] = attachment
        return attachment

    async def get_by_id(
        self, workspace_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> Attachment | None:
        attachment = self.attachments.get(attachment_id)
        if (
            attachment is None
            or attachment.workspace_id != workspace_id
            or attachment.deleted_at is not None
        ):
            return None
        return attachment

    async def list_by_issue(self, issue_id: uuid.UUID) -> Sequence[Attachment]:
        return [
            a for a in self.attachments.values() if a.issue_id == issue_id and a.deleted_at is None
        ]

    async def list_by_comment(self, comment_id: uuid.UUID) -> Sequence[Attachment]:
        return [
            a
            for a in self.attachments.values()
            if a.comment_id == comment_id and a.deleted_at is None
        ]

    async def soft_delete(self, attachment_id: uuid.UUID) -> None:
        attachment = self.attachments.get(attachment_id)
        if attachment is not None:
            attachment.deleted_at = datetime.now(UTC)


class FakeStorageProvider:
    """Implementa `StorageProvider` (`core/storage.py`) em memória — nenhum I/O
    de disco real nos testes unitários de `AttachmentService`.
    """

    provider_name = "fake"

    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}
        self.deleted: list[str] = []

    async def save(self, *, stream: BinaryIO, suggested_name: str) -> str:
        storage_key = f"{uuid.uuid4().hex}-{suggested_name}"
        self.saved[storage_key] = stream.read()
        return storage_key

    async def open(self, storage_key: str) -> str:
        return storage_key

    async def delete(self, storage_key: str) -> None:
        self.deleted.append(storage_key)
        self.saved.pop(storage_key, None)
