import secrets
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.core.authorization import PermissionService
from src.core.config import Settings
from src.core.security import CurrentUser, generate_invitation_token, hash_invitation_token
from src.core.slug import slugify
from src.features.auth.repository import UserRepositoryProtocol
from src.features.workspaces.exceptions import (
    AlreadyMemberError,
    CannotLeaveAsSoleOwnerError,
    CannotManageOwnMembershipError,
    InvitationAlreadyPendingError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
    MemberNotFoundError,
    SlugTakenError,
    WorkspaceNotFoundError,
)
from src.features.workspaces.models import (
    Invitation,
    Workspace,
    WorkspaceActivityLog,
    WorkspaceMember,
    WorkspaceRole,
)
from src.features.workspaces.repository import (
    InvitationRepositoryProtocol,
    WorkspaceRepositoryProtocol,
)
from src.features.workspaces.schemas import (
    InvitationCreateRequest,
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
)

_SLUG_COLLISION_RETRIES = 5


@dataclass(frozen=True)
class InvitationIssued:
    invitation: Invitation
    token: str


class WorkspaceService:
    def __init__(
        self, workspace_repo: WorkspaceRepositoryProtocol, permission_service: PermissionService
    ) -> None:
        """Autorização (posse de tenant e papel) não é mais checada aqui — o
        router já resolveu `Depends(require_permission(...))` antes deste
        service ser chamado (ver `core/authorization.py`, Sprint 5). Este
        service só recebe `permission_service` para checagens contextuais que
        dependem de um recurso já buscado (`require_can_manage_member`), que
        não são resolvíveis apenas a partir do path da requisição.
        """
        self._workspace_repo = workspace_repo
        self._permission_service = permission_service

    async def create(self, current_user: CurrentUser, payload: WorkspaceCreateRequest) -> Workspace:
        slug = await self._resolve_slug(payload.name, payload.slug)
        workspace = await self._workspace_repo.create(
            Workspace(
                name=payload.name,
                slug=slug,
                description=payload.description,
                owner_id=current_user.id,
            )
        )
        await self._workspace_repo.add_member(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=current_user.id, role=WorkspaceRole.OWNER
            )
        )
        await self._record_activity(
            workspace.id, current_user.id, "workspace.created", {"name": workspace.name}
        )
        return workspace

    async def list_for_user(
        self, current_user: CurrentUser, *, page: int, per_page: int
    ) -> tuple[Sequence[Workspace], int]:
        workspaces = await self._workspace_repo.list_by_user(
            current_user.id, page=page, per_page=per_page
        )
        total = await self._workspace_repo.count_by_user(current_user.id)
        return workspaces, total

    async def get(self, workspace_id: uuid.UUID) -> Workspace:
        return await self._get_active_workspace(workspace_id)

    async def update(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: WorkspaceUpdateRequest
    ) -> Workspace:
        workspace = await self._get_active_workspace(workspace_id)

        changes: dict[str, dict[str, object]] = {}
        if payload.name is not None and payload.name != workspace.name:
            changes["name"] = {"old": workspace.name, "new": payload.name}
            workspace.name = payload.name
        if payload.description is not None and payload.description != workspace.description:
            changes["description"] = {"old": workspace.description, "new": payload.description}
            workspace.description = payload.description
        if payload.slug is not None and payload.slug != workspace.slug:
            existing = await self._workspace_repo.get_by_slug(payload.slug)
            if existing is not None and existing.id != workspace.id:
                raise SlugTakenError()
            changes["slug"] = {"old": workspace.slug, "new": payload.slug}
            workspace.slug = payload.slug

        if changes:
            await self._workspace_repo.update(workspace)
            await self._record_activity(workspace.id, current_user.id, "workspace.updated", changes)
        return workspace

    async def delete(self, current_user: CurrentUser, workspace_id: uuid.UUID) -> None:
        workspace = await self._get_active_workspace(workspace_id)

        await self._workspace_repo.soft_delete(workspace_id)
        await self._record_activity(
            workspace_id, current_user.id, "workspace.deleted", {"name": workspace.name}
        )

    async def list_members(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
        role: WorkspaceRole | None,
    ) -> tuple[Sequence[WorkspaceMember], int]:
        members = await self._workspace_repo.list_members(
            workspace_id, page=page, per_page=per_page, role=role
        )
        total = await self._workspace_repo.count_members(workspace_id, role=role)
        return members, total

    async def leave(self, current_user: CurrentUser, workspace_id: uuid.UUID) -> None:
        member = await self._workspace_repo.get_member(workspace_id, current_user.id)
        if member is None:
            raise WorkspaceNotFoundError()

        if member.role == WorkspaceRole.OWNER:
            owner_count = await self._workspace_repo.count_members(
                workspace_id, role=WorkspaceRole.OWNER
            )
            if owner_count <= 1:
                raise CannotLeaveAsSoleOwnerError()

        await self._workspace_repo.remove_member(member.id)
        await self._record_activity(
            workspace_id, current_user.id, "member.left", {"user_id": str(current_user.id)}
        )

    async def update_member_role(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        member_id: uuid.UUID,
        new_role: WorkspaceRole,
        acting_role: WorkspaceRole,
    ) -> WorkspaceMember:
        """`acting_role` já veio autorizado por `Depends(require_permission(...))`
        para a permissão base (`member.update_role`) — o que falta checar aqui é
        a regra contextual que depende do papel do alvo (`require_can_manage_member`),
        só conhecida depois de buscar a `WorkspaceMember` a ser alterada.
        """
        target = await self._workspace_repo.get_member_by_id(workspace_id, member_id)
        if target is None:
            raise MemberNotFoundError()
        if target.user_id == current_user.id:
            raise CannotManageOwnMembershipError()

        self._permission_service.require_can_manage_member(
            actor_role=acting_role, target_role=target.role
        )

        old_role = target.role
        updated = await self._workspace_repo.update_member_role(target, new_role)
        await self._record_activity(
            workspace_id,
            current_user.id,
            "member.role_changed",
            {"member_id": str(member_id), "old_role": old_role.value, "new_role": new_role.value},
        )
        return updated

    async def remove_member(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        member_id: uuid.UUID,
        acting_role: WorkspaceRole,
    ) -> None:
        target = await self._workspace_repo.get_member_by_id(workspace_id, member_id)
        if target is None:
            raise MemberNotFoundError()
        if target.user_id == current_user.id:
            raise CannotManageOwnMembershipError()

        self._permission_service.require_can_manage_member(
            actor_role=acting_role, target_role=target.role
        )

        await self._workspace_repo.remove_member(target.id)
        await self._record_activity(
            workspace_id,
            current_user.id,
            "member.removed",
            {"member_id": str(member_id), "role": target.role.value},
        )

    async def _get_active_workspace(self, workspace_id: uuid.UUID) -> Workspace:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError()
        return workspace

    async def _resolve_slug(self, name: str, requested_slug: str | None) -> str:
        if requested_slug is not None:
            if await self._workspace_repo.get_by_slug(requested_slug) is not None:
                raise SlugTakenError()
            return requested_slug

        base = slugify(name)
        candidate = base
        for _ in range(_SLUG_COLLISION_RETRIES):
            if await self._workspace_repo.get_by_slug(candidate) is None:
                return candidate
            candidate = f"{base}-{secrets.token_hex(3)}"
        raise SlugTakenError()

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        await self._workspace_repo.record_activity(
            WorkspaceActivityLog(
                workspace_id=workspace_id,
                actor_id=actor_id,
                action=action,
                metadata_=dict(metadata) if metadata is not None else None,
            )
        )


class InvitationService:
    def __init__(
        self,
        invitation_repo: InvitationRepositoryProtocol,
        workspace_repo: WorkspaceRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
        settings: Settings,
    ) -> None:
        self._invitation_repo = invitation_repo
        self._workspace_repo = workspace_repo
        self._user_repo = user_repo
        self._settings = settings

    async def create(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: InvitationCreateRequest
    ) -> InvitationIssued:
        email = payload.email.lower()
        invited_user = await self._user_repo.get_by_email(email)
        if invited_user is not None:
            existing_member = await self._workspace_repo.get_member(workspace_id, invited_user.id)
            if existing_member is not None:
                raise AlreadyMemberError()

        if await self._invitation_repo.get_pending_by_email(workspace_id, email) is not None:
            raise InvitationAlreadyPendingError()

        token = generate_invitation_token()
        invitation = await self._invitation_repo.create(
            Invitation(
                workspace_id=workspace_id,
                email=email,
                role=payload.role,
                token_hash=hash_invitation_token(token),
                invited_by_id=current_user.id,
                expires_at=datetime.now(UTC)
                + timedelta(days=self._settings.invitation_expire_days),
            )
        )
        await self._record_activity(
            workspace_id,
            current_user.id,
            "invitation.sent",
            {"email": email, "role": payload.role.value},
        )
        return InvitationIssued(invitation=invitation, token=token)

    async def list_for_workspace(
        self, workspace_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[Sequence[Invitation], int]:
        invitations = await self._invitation_repo.list_by_workspace(
            workspace_id, page=page, per_page=per_page
        )
        total = await self._invitation_repo.count_by_workspace(workspace_id)
        return invitations, total

    async def cancel(self, workspace_id: uuid.UUID, invitation_id: uuid.UUID) -> None:
        invitation = await self._invitation_repo.get_by_id(workspace_id, invitation_id)
        if invitation is None:
            raise InvitationNotFoundError()

        await self._invitation_repo.cancel(invitation_id)

    async def accept(self, current_user: CurrentUser, token: str) -> WorkspaceMember:
        invitation = await self._invitation_repo.get_by_token_hash(hash_invitation_token(token))
        if invitation is None:
            raise InvitationNotFoundError()

        if invitation.accepted_at is not None or invitation.expires_at < datetime.now(UTC):
            raise InvitationExpiredError()

        if invitation.email.lower() != current_user.email.lower():
            raise InvitationEmailMismatchError()

        already_member = await self._workspace_repo.get_member(
            invitation.workspace_id, current_user.id
        )
        if already_member is not None:
            raise AlreadyMemberError()

        member = await self._workspace_repo.add_member(
            WorkspaceMember(
                workspace_id=invitation.workspace_id, user_id=current_user.id, role=invitation.role
            )
        )
        # `add_member` não faz `selectinload(WorkspaceMember.user)` — a resposta HTTP
        # (`WorkspaceMemberResponse.from_member`) precisa do `User` completo, e um
        # lazy-load implícito quebraria sob SQLAlchemy async (`MissingGreenlet`).
        # Anexar aqui em vez de recarregar com outra query.
        full_user = await self._user_repo.get_by_id(current_user.id)
        assert full_user is not None  # já validado por get_current_user nesta mesma requisição
        member.user = full_user
        await self._invitation_repo.mark_accepted(invitation.id)
        await self._record_activity(
            invitation.workspace_id,
            current_user.id,
            "invitation.accepted",
            {"invitation_id": str(invitation.id)},
        )
        return member

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        await self._workspace_repo.record_activity(
            WorkspaceActivityLog(
                workspace_id=workspace_id,
                actor_id=actor_id,
                action=action,
                metadata_=dict(metadata) if metadata is not None else None,
            )
        )
