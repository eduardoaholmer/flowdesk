import re
import secrets
import unicodedata
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.core.config import Settings
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser, generate_invitation_token, hash_invitation_token
from src.features.auth.repository import UserRepositoryProtocol
from src.features.workspaces.exceptions import (
    AlreadyMemberError,
    CannotLeaveAsSoleOwnerError,
    InvitationAlreadyPendingError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
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

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_MIN_LENGTH = 3
_SLUG_MAX_LENGTH = 50
_SLUG_COLLISION_RETRIES = 5


@dataclass(frozen=True)
class InvitationIssued:
    invitation: Invitation
    token: str


def _slugify(name: str) -> str:
    """Melhor esforço de transliteração (`unicodedata`, sem dependência externa
    tipo `python-slugify`) — não precisa ser perfeito para todo alfabeto, só
    determinístico o bastante para reduzir colisão antes do fallback de sufixo.
    """
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) < _SLUG_MIN_LENGTH:
        slug = f"{slug}-{secrets.token_hex(3)}" if slug else secrets.token_hex(4)
    return slug[:_SLUG_MAX_LENGTH].strip("-")


async def _require_member(
    workspace_repo: WorkspaceRepositoryProtocol, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> WorkspaceMember:
    """Checagem de posse compartilhada por todo método de service desta feature
    (`CLAUDE.md` §6): não-membro recebe o mesmo `WorkspaceNotFoundError` de
    workspace inexistente — nunca confirmamos existência a quem não participa.
    """
    member = await workspace_repo.get_member(workspace_id, user_id)
    if member is None:
        raise WorkspaceNotFoundError()
    return member


def _require_role(member: WorkspaceMember, *allowed: WorkspaceRole) -> None:
    """Checagem mínima de papel usada nesta sprint — `CLAUDE.md` §10 pede
    `Depends(require_permission(...))` sobre uma matriz central em
    `core/authorization.py`, mas essa infraestrutura de RBAC é escopo explícito
    da Sprint 5 (ver ADR-009). Isolada aqui como função pura, sem estado de
    protocolo HTTP, para ser um ponto de substituição único quando a Sprint 5
    chegar — nenhum outro lugar do código reimplementa essa checagem.
    """
    if member.role not in allowed:
        raise PermissionDeniedError()


class WorkspaceService:
    def __init__(self, workspace_repo: WorkspaceRepositoryProtocol) -> None:
        self._workspace_repo = workspace_repo

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

    async def get(self, current_user: CurrentUser, workspace_id: uuid.UUID) -> Workspace:
        workspace = await self._get_active_workspace(workspace_id)
        await _require_member(self._workspace_repo, workspace_id, current_user.id)
        return workspace

    async def update(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: WorkspaceUpdateRequest
    ) -> Workspace:
        workspace = await self._get_active_workspace(workspace_id)
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)
        _require_role(member, WorkspaceRole.OWNER)

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
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)
        _require_role(member, WorkspaceRole.OWNER)

        await self._workspace_repo.soft_delete(workspace_id)
        await self._record_activity(
            workspace_id, current_user.id, "workspace.deleted", {"name": workspace.name}
        )

    async def list_members(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
        role: WorkspaceRole | None,
    ) -> tuple[Sequence[WorkspaceMember], int]:
        await self._get_active_workspace(workspace_id)
        await _require_member(self._workspace_repo, workspace_id, current_user.id)
        members = await self._workspace_repo.list_members(
            workspace_id, page=page, per_page=per_page, role=role
        )
        total = await self._workspace_repo.count_members(workspace_id, role=role)
        return members, total

    async def leave(self, current_user: CurrentUser, workspace_id: uuid.UUID) -> None:
        await self._get_active_workspace(workspace_id)
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)

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

        base = _slugify(name)
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
        await self._get_active_workspace(workspace_id)
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)
        _require_role(member, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

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
        self, current_user: CurrentUser, workspace_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[Sequence[Invitation], int]:
        await self._get_active_workspace(workspace_id)
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)
        _require_role(member, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

        invitations = await self._invitation_repo.list_by_workspace(
            workspace_id, page=page, per_page=per_page
        )
        total = await self._invitation_repo.count_by_workspace(workspace_id)
        return invitations, total

    async def cancel(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> None:
        await self._get_active_workspace(workspace_id)
        member = await _require_member(self._workspace_repo, workspace_id, current_user.id)
        _require_role(member, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

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

    async def _get_active_workspace(self, workspace_id: uuid.UUID) -> Workspace:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError()
        return workspace

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
