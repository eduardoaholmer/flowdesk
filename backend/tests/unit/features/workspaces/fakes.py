import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.features.workspaces.models import (
    Invitation,
    Workspace,
    WorkspaceActivityLog,
    WorkspaceMember,
    WorkspaceRole,
)
from uuid6 import uuid7


class FakeWorkspaceRepository:
    """Implementa `WorkspaceRepositoryProtocol` em memória (`CLAUDE.md` §5/§6) —
    mesmo racional de `tests/unit/features/auth/fakes.py`: testar o service sem
    banco, simulando os defaults que só existem no flush do SQLAlchemy real.
    """

    def __init__(self) -> None:
        self.workspaces: dict[uuid.UUID, Workspace] = {}
        self.members: dict[uuid.UUID, WorkspaceMember] = {}
        self.activity_log: list[WorkspaceActivityLog] = []

    async def create(self, workspace: Workspace) -> Workspace:
        if workspace.id is None:
            workspace.id = uuid7()
        now = datetime.now(UTC)
        workspace.created_at = workspace.created_at or now
        workspace.updated_at = workspace.updated_at or now
        self.workspaces[workspace.id] = workspace
        return workspace

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None or workspace.deleted_at is not None:
            return None
        return workspace

    async def get_by_slug(self, slug: str) -> Workspace | None:
        for workspace in self.workspaces.values():
            if workspace.slug == slug and workspace.deleted_at is None:
                return workspace
        return None

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Workspace]:
        workspace_ids = {
            m.workspace_id
            for m in self.members.values()
            if m.user_id == user_id and m.deleted_at is None
        }
        matches = [
            w for w in self.workspaces.values() if w.id in workspace_ids and w.deleted_at is None
        ]
        matches.sort(key=lambda w: w.created_at, reverse=True)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        return len(await self.list_by_user(user_id, page=1, per_page=len(self.workspaces) or 1))

    async def update(self, workspace: Workspace) -> Workspace:
        workspace.updated_at = datetime.now(UTC)
        return workspace

    async def soft_delete(self, workspace_id: uuid.UUID) -> None:
        workspace = self.workspaces.get(workspace_id)
        if workspace is not None:
            workspace.deleted_at = datetime.now(UTC)

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        if member.id is None:
            member.id = uuid7()
        member.created_at = member.created_at or datetime.now(UTC)
        self.members[member.id] = member
        return member

    async def get_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceMember | None:
        for member in self.members.values():
            if (
                member.workspace_id == workspace_id
                and member.user_id == user_id
                and member.deleted_at is None
            ):
                return member
        return None

    async def list_members(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        role: WorkspaceRole | None = None,
    ) -> Sequence[WorkspaceMember]:
        matches = [
            m
            for m in self.members.values()
            if m.workspace_id == workspace_id
            and m.deleted_at is None
            and (role is None or m.role == role)
        ]
        matches.sort(key=lambda m: m.created_at)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_members(
        self, workspace_id: uuid.UUID, *, role: WorkspaceRole | None = None
    ) -> int:
        return len(
            [
                m
                for m in self.members.values()
                if m.workspace_id == workspace_id
                and m.deleted_at is None
                and (role is None or m.role == role)
            ]
        )

    async def remove_member(self, member_id: uuid.UUID) -> None:
        member = self.members.get(member_id)
        if member is not None:
            member.deleted_at = datetime.now(UTC)

    async def list_memberships_by_user(self, user_id: uuid.UUID) -> Sequence[WorkspaceMember]:
        return [
            m
            for m in self.members.values()
            if m.user_id == user_id
            and m.deleted_at is None
            and self.workspaces[m.workspace_id].deleted_at is None
        ]

    async def record_activity(self, entry: WorkspaceActivityLog) -> WorkspaceActivityLog:
        if entry.id is None:
            entry.id = uuid7()
        entry.created_at = entry.created_at or datetime.now(UTC)
        self.activity_log.append(entry)
        return entry


class FakeInvitationRepository:
    def __init__(self) -> None:
        self.invitations: dict[uuid.UUID, Invitation] = {}

    async def create(self, invitation: Invitation) -> Invitation:
        if invitation.id is None:
            invitation.id = uuid7()
        invitation.created_at = invitation.created_at or datetime.now(UTC)
        self.invitations[invitation.id] = invitation
        return invitation

    async def get_by_id(
        self, workspace_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> Invitation | None:
        invitation = self.invitations.get(invitation_id)
        if (
            invitation is None
            or invitation.workspace_id != workspace_id
            or invitation.deleted_at is not None
        ):
            return None
        return invitation

    async def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        for invitation in self.invitations.values():
            if invitation.token_hash == token_hash and invitation.deleted_at is None:
                return invitation
        return None

    async def get_pending_by_email(self, workspace_id: uuid.UUID, email: str) -> Invitation | None:
        for invitation in self.invitations.values():
            if (
                invitation.workspace_id == workspace_id
                and invitation.email == email
                and invitation.accepted_at is None
                and invitation.deleted_at is None
            ):
                return invitation
        return None

    async def list_by_workspace(
        self, workspace_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Invitation]:
        matches = [
            i
            for i in self.invitations.values()
            if i.workspace_id == workspace_id and i.deleted_at is None
        ]
        matches.sort(key=lambda i: i.created_at, reverse=True)
        start = (page - 1) * per_page
        return matches[start : start + per_page]

    async def count_by_workspace(self, workspace_id: uuid.UUID) -> int:
        return len(
            [
                i
                for i in self.invitations.values()
                if i.workspace_id == workspace_id and i.deleted_at is None
            ]
        )

    async def cancel(self, invitation_id: uuid.UUID) -> None:
        invitation = self.invitations.get(invitation_id)
        if invitation is not None:
            invitation.deleted_at = datetime.now(UTC)

    async def mark_accepted(self, invitation_id: uuid.UUID) -> None:
        invitation = self.invitations.get(invitation_id)
        if invitation is not None:
            invitation.accepted_at = datetime.now(UTC)
