import uuid
from typing import BinaryIO

from src.core.authorization import PermissionService
from src.core.permissions import Permission
from src.core.security import CurrentUser
from src.core.storage import StorageProvider
from src.features.attachments.exceptions import (
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    AttachmentTypeNotAllowedError,
)
from src.features.attachments.models import Attachment
from src.features.attachments.repository import AttachmentRepositoryProtocol
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.models import ActivityLog
from src.features.issues.repository import IssueRepositoryProtocol
from src.features.workspaces.models import WorkspaceMember


class AttachmentService:
    def __init__(
        self,
        attachment_repo: AttachmentRepositoryProtocol,
        issue_repo: IssueRepositoryProtocol,
        storage: StorageProvider,
        permission_service: PermissionService,
        *,
        max_size_bytes: int,
        allowed_content_types: frozenset[str],
    ) -> None:
        """`max_size_bytes`/`allowed_content_types` chegam via `Settings`
        (Depends) em vez de serem lidos direto de `get_settings()` aqui — o
        service permanece testável com valores arbitrários sem monkeypatch de
        configuração global (`CLAUDE.md` §5, testabilidade via injeção).

        Só suporta anexar a uma Issue nesta sprint (`POST .../issues/{id}/attachments`,
        pedido literal do enunciado) — o schema já modela `comment_id` como
        alvo alternativo (polimorfismo pré-existente desde a Sprint 2), mas
        anexar diretamente a um comentário fica para quando o enunciado pedir
        (ver ADR-013, "Impacto futuro").
        """
        self._attachment_repo = attachment_repo
        self._issue_repo = issue_repo
        self._storage = storage
        self._permission_service = permission_service
        self._max_size_bytes = max_size_bytes
        self._allowed_content_types = allowed_content_types

    async def upload_to_issue(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        *,
        file_name: str,
        content_type: str,
        size: int,
        stream: BinaryIO,
    ) -> Attachment:
        await self._get_active_issue(workspace_id, issue_id)
        self._validate(content_type, size)

        storage_key = await self._storage.save(stream=stream, suggested_name=file_name)
        attachment = await self._attachment_repo.create(
            Attachment(
                workspace_id=workspace_id,
                issue_id=issue_id,
                uploader_id=current_user.id,
                file_name=file_name,
                content_type=content_type,
                file_size=size,
                storage_key=storage_key,
                storage_provider=self._storage.provider_name,
            )
        )
        await self._record_activity(
            workspace_id, issue_id, current_user.id, "attachment.uploaded", new_value=file_name
        )
        return attachment

    async def get(self, workspace_id: uuid.UUID, attachment_id: uuid.UUID) -> Attachment:
        return await self._get_active_attachment(workspace_id, attachment_id)

    async def list_for_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> list[Attachment]:
        await self._get_active_issue(workspace_id, issue_id)
        return list(await self._attachment_repo.list_by_issue(issue_id))

    async def delete(
        self,
        acting_member: WorkspaceMember,
        workspace_id: uuid.UUID,
        attachment_id: uuid.UUID,
    ) -> None:
        attachment = await self._get_active_attachment(workspace_id, attachment_id)
        self._permission_service.require(
            member=acting_member,
            permission=Permission.ATTACHMENT_DELETE,
            resource_owner_id=attachment.uploader_id,
        )

        await self._attachment_repo.soft_delete(attachment_id)
        # Melhor esforço: a linha soft-deletada (dado de auditoria) é a fonte
        # de verdade; falha ao apagar o blob físico não deve impedir a
        # exclusão lógica de completar (o arquivo órfão é um custo de
        # armazenamento, não uma inconsistência de domínio visível ao usuário).
        await self._storage.delete(attachment.storage_key)

        issue_id = attachment.issue_id
        if issue_id is not None:
            await self._record_activity(
                workspace_id,
                issue_id,
                acting_member.user_id,
                "attachment.deleted",
                old_value=attachment.file_name,
            )

    def _validate(self, content_type: str, size: int) -> None:
        if size > self._max_size_bytes:
            raise AttachmentTooLargeError()
        if content_type not in self._allowed_content_types:
            raise AttachmentTypeNotAllowedError()

    async def _get_active_issue(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> None:
        if await self._issue_repo.get_by_id(workspace_id, issue_id) is None:
            raise IssueNotFoundError()

    async def _get_active_attachment(
        self, workspace_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> Attachment:
        attachment = await self._attachment_repo.get_by_id(workspace_id, attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError()
        return attachment

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        *,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> None:
        await self._issue_repo.record_activity(
            ActivityLog(
                workspace_id=workspace_id,
                issue_id=issue_id,
                actor_id=actor_id,
                action=action,
                old_value=old_value,
                new_value=new_value,
            )
        )
