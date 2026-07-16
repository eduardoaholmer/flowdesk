import re
import uuid
from collections.abc import Sequence

from src.core.authorization import PermissionService
from src.core.permissions import Permission
from src.core.security import CurrentUser
from src.features.comments.exceptions import CommentNotFoundError
from src.features.comments.models import Comment
from src.features.comments.repository import CommentRepositoryProtocol
from src.features.comments.schemas import CommentCreateRequest, CommentUpdateRequest
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.models import ActivityLog, Issue
from src.features.issues.repository import IssueRepositoryProtocol
from src.features.notifications.models import NotificationType
from src.features.notifications.service import NotificationService
from src.features.workspaces.models import WorkspaceMember
from src.features.workspaces.repository import WorkspaceRepositoryProtocol

# Sintaxe de menção desta sprint: `@` seguido do local-part do e-mail do
# membro (parte antes do `@`), não do nome de exibição — nomes têm espaço e
# não são únicos, e-mail já é a identidade única do sistema (`docs/03-database.md`
# §8). Evita precisar de uma UI de autocomplete nesta sprint (fora de escopo,
# "arquitetura preparada" — ver ADR-013) sem introduzir ambiguidade de match.
_MENTION_RE = re.compile(r"@([A-Za-z0-9._%+-]+)")
_PREVIEW_LENGTH = 140
# Teto de membros considerados na resolução de menções por comentário — uma
# única query (`list_members`), não uma por menção (evita N+1). Suficiente
# para a escala de workspace deste projeto; workspaces muito maiores
# exigiriam trocar por uma busca indexada por local-part (melhoria futura,
# ver `docs/09-decision-log.md` ADR-013).
_MENTION_MEMBER_LOOKUP_LIMIT = 200


def _preview(body: str) -> str:
    stripped = body.strip()
    if len(stripped) <= _PREVIEW_LENGTH:
        return stripped
    return f"{stripped[:_PREVIEW_LENGTH]}…"


class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepositoryProtocol,
        issue_repo: IssueRepositoryProtocol,
        workspace_repo: WorkspaceRepositoryProtocol,
        permission_service: PermissionService,
        notification_service: NotificationService,
    ) -> None:
        """Recebe `PermissionService`, mesmo racional de `IssueService`:
        editar/excluir comentário tem posse-como-exceção (`Permission.COMMENT_UPDATE`/
        `.COMMENT_DELETE` estão em `OWNERSHIP_OVERRIDE_PERMISSIONS`), uma
        checagem contextual só resolvível depois que o comentário já foi
        buscado.

        `issue_repo` valida que a issue existe/está ativa e é o dono de
        `ActivityLog` (comentários não têm timeline própria — todo evento de
        comentário aparece na timeline da Issue-mãe, ver ADR-013).
        `workspace_repo` resolve os membros do workspace para detecção de
        menções (`_resolve_mentions`).
        `notification_service` (Sprint 9) é o *service* público de outra
        feature, não o repository — padrão explícito de `docs/02-architecture.md`
        para efeito colateral entre features.
        """
        self._comment_repo = comment_repo
        self._issue_repo = issue_repo
        self._workspace_repo = workspace_repo
        self._permission_service = permission_service
        self._notification_service = notification_service

    async def create(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        payload: CommentCreateRequest,
    ) -> Comment:
        issue = await self._get_active_issue(workspace_id, issue_id)

        comment = await self._comment_repo.create(
            Comment(
                workspace_id=workspace_id,
                issue_id=issue_id,
                author_id=current_user.id,
                body=payload.body,
            )
        )
        mentioned_ids = await self._resolve_mentions(workspace_id, payload.body)
        if mentioned_ids:
            await self._comment_repo.add_mentions(comment.id, mentioned_ids)
        await self._comment_repo.refresh_mentions(comment)
        await self._notify_mentions(current_user, issue, comment, mentioned_ids)

        await self._record_activity(
            workspace_id,
            issue_id,
            current_user.id,
            "comment.created",
            new_value=_preview(comment.body),
        )
        return comment

    async def list_for_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[Sequence[Comment], int]:
        await self._get_active_issue(workspace_id, issue_id)
        comments = await self._comment_repo.list_by_issue(issue_id, page=page, per_page=per_page)
        total = await self._comment_repo.count_by_issue(issue_id)
        return comments, total

    async def update(
        self,
        acting_member: WorkspaceMember,
        workspace_id: uuid.UUID,
        comment_id: uuid.UUID,
        payload: CommentUpdateRequest,
    ) -> Comment:
        comment = await self._get_active_comment(workspace_id, comment_id)
        self._permission_service.require(
            member=acting_member,
            permission=Permission.COMMENT_UPDATE,
            resource_owner_id=comment.author_id,
        )

        old_preview = _preview(comment.body)
        comment.body = payload.body
        mentioned_ids = await self._resolve_mentions(workspace_id, payload.body)
        await self._comment_repo.replace_mentions(comment.id, mentioned_ids)
        await self._comment_repo.update(comment)
        await self._comment_repo.refresh_mentions(comment)

        await self._record_activity(
            workspace_id,
            comment.issue_id,
            acting_member.user_id,
            "comment.updated",
            old_value=old_preview,
            new_value=_preview(comment.body),
        )
        return comment

    async def delete(
        self, acting_member: WorkspaceMember, workspace_id: uuid.UUID, comment_id: uuid.UUID
    ) -> None:
        comment = await self._get_active_comment(workspace_id, comment_id)
        self._permission_service.require(
            member=acting_member,
            permission=Permission.COMMENT_DELETE,
            resource_owner_id=comment.author_id,
        )
        await self._comment_repo.soft_delete(comment_id)
        await self._record_activity(
            workspace_id,
            comment.issue_id,
            acting_member.user_id,
            "comment.deleted",
            old_value=_preview(comment.body),
        )

    async def _get_active_issue(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue:
        issue = await self._issue_repo.get_by_id(workspace_id, issue_id)
        if issue is None:
            raise IssueNotFoundError()
        return issue

    async def _get_active_comment(self, workspace_id: uuid.UUID, comment_id: uuid.UUID) -> Comment:
        comment = await self._comment_repo.get_by_id(workspace_id, comment_id)
        if comment is None:
            raise CommentNotFoundError()
        return comment

    async def _resolve_mentions(self, workspace_id: uuid.UUID, body: str) -> list[uuid.UUID]:
        tokens = {match.group(1).lower() for match in _MENTION_RE.finditer(body)}
        if not tokens:
            return []

        members = await self._workspace_repo.list_members(
            workspace_id, page=1, per_page=_MENTION_MEMBER_LOOKUP_LIMIT
        )
        return [
            member.user_id
            for member in members
            if member.user.email.split("@", 1)[0].lower() in tokens
        ]

    async def _notify_mentions(
        self,
        current_user: CurrentUser,
        issue: Issue,
        comment: Comment,
        mentioned_ids: list[uuid.UUID],
    ) -> None:
        """Não notifica o próprio autor caso ele se auto-mencione — o `CommentMention`
        continua registrado normalmente (§8.4 `docs/03-database.md`), só a notificação
        em si é pulada, mesmo racional de `IssueService._notify_status_change`."""
        for mentioned_user_id in mentioned_ids:
            if mentioned_user_id == current_user.id:
                continue
            await self._notification_service.notify(
                user_id=mentioned_user_id,
                workspace_id=issue.workspace_id,
                notification_type=NotificationType.MENTION,
                payload={
                    "issue_id": str(issue.id),
                    "issue_identifier": issue.identifier,
                    "comment_id": str(comment.id),
                    "actor_name": current_user.name,
                    "preview": _preview(comment.body),
                },
            )

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
