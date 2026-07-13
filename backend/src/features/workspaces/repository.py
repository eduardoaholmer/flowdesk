import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.workspaces.models import Invitation, Workspace, WorkspaceMember


class WorkspaceRepositoryProtocol(Protocol):
    async def create(self, workspace: Workspace) -> Workspace: ...
    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None: ...
    async def get_by_slug(self, slug: str) -> Workspace | None: ...
    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Workspace]: ...
    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember: ...
    async def get_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceMember | None: ...
    async def list_members(self, workspace_id: uuid.UUID) -> Sequence[WorkspaceMember]: ...


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workspace: Workspace) -> Workspace:
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
        result: Workspace | None = await self._session.scalar(stmt)
        return result

    async def get_by_slug(self, slug: str) -> Workspace | None:
        stmt = select(Workspace).where(Workspace.slug == slug, Workspace.deleted_at.is_(None))
        result: Workspace | None = await self._session.scalar(stmt)
        return result

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
                Workspace.deleted_at.is_(None),
            )
        )
        return (await self._session.scalars(stmt)).all()

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self._session.add(member)
        await self._session.flush()
        return member

    async def get_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceMember | None:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.deleted_at.is_(None),
        )
        result: WorkspaceMember | None = await self._session.scalar(stmt)
        return result

    async def list_members(self, workspace_id: uuid.UUID) -> Sequence[WorkspaceMember]:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.deleted_at.is_(None)
        )
        return (await self._session.scalars(stmt)).all()


class InvitationRepositoryProtocol(Protocol):
    async def create(self, invitation: Invitation) -> Invitation: ...
    async def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...
    async def get_pending_by_email(
        self, workspace_id: uuid.UUID, email: str
    ) -> Invitation | None: ...


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, invitation: Invitation) -> Invitation:
        self._session.add(invitation)
        await self._session.flush()
        return invitation

    async def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.token_hash == token_hash, Invitation.deleted_at.is_(None)
        )
        result: Invitation | None = await self._session.scalar(stmt)
        return result

    async def get_pending_by_email(self, workspace_id: uuid.UUID, email: str) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.workspace_id == workspace_id,
            Invitation.email == email,
            Invitation.accepted_at.is_(None),
            Invitation.deleted_at.is_(None),
        )
        result: Invitation | None = await self._session.scalar(stmt)
        return result
