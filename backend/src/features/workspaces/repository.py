import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.features.workspaces.models import (
    Invitation,
    Workspace,
    WorkspaceActivityLog,
    WorkspaceMember,
    WorkspaceRole,
)


class WorkspaceRepositoryProtocol(Protocol):
    async def create(self, workspace: Workspace) -> Workspace: ...
    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None: ...
    async def get_by_slug(self, slug: str) -> Workspace | None: ...
    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Workspace]: ...
    async def count_by_user(self, user_id: uuid.UUID) -> int: ...
    async def update(self, workspace: Workspace) -> Workspace: ...
    async def soft_delete(self, workspace_id: uuid.UUID) -> None: ...
    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember: ...
    async def get_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceMember | None: ...
    async def get_member_by_id(
        self, workspace_id: uuid.UUID, member_id: uuid.UUID
    ) -> WorkspaceMember | None: ...
    async def update_member_role(
        self, member: WorkspaceMember, role: WorkspaceRole
    ) -> WorkspaceMember: ...
    async def list_members(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        role: WorkspaceRole | None = None,
    ) -> Sequence[WorkspaceMember]: ...
    async def count_members(
        self, workspace_id: uuid.UUID, *, role: WorkspaceRole | None = None
    ) -> int: ...
    async def remove_member(self, member_id: uuid.UUID) -> None: ...
    async def list_memberships_by_user(self, user_id: uuid.UUID) -> Sequence[WorkspaceMember]: ...
    async def record_activity(self, entry: WorkspaceActivityLog) -> WorkspaceActivityLog: ...


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

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
                Workspace.deleted_at.is_(None),
            )
            .order_by(Workspace.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
                Workspace.deleted_at.is_(None),
            )
        )
        return (await self._session.scalar(stmt)) or 0

    async def update(self, workspace: Workspace) -> Workspace:
        """Persiste mutações feitas pelo service em um `Workspace` já rastreado
        pela sessão (retornado por `get_by_id`) — nenhum SQL de `UPDATE` explícito
        é necessário, o `flush()` já emite o `UPDATE` a partir do dirty-tracking
        do SQLAlchemy.
        """
        await self._session.flush()
        return workspace

    async def soft_delete(self, workspace_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Workspace)
            .where(Workspace.id == workspace_id)
            .values(deleted_at=datetime.now(UTC))
        )

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

    async def get_member_by_id(
        self, workspace_id: uuid.UUID, member_id: uuid.UUID
    ) -> WorkspaceMember | None:
        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.deleted_at.is_(None),
            )
            .options(selectinload(WorkspaceMember.user))
        )
        result: WorkspaceMember | None = await self._session.scalar(stmt)
        return result

    async def update_member_role(
        self, member: WorkspaceMember, role: WorkspaceRole
    ) -> WorkspaceMember:
        member.role = role
        await self._session.flush()
        return member

    async def list_members(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        role: WorkspaceRole | None = None,
    ) -> Sequence[WorkspaceMember]:
        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.deleted_at.is_(None)
            )
            .options(selectinload(WorkspaceMember.user))
            .order_by(WorkspaceMember.created_at.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        if role is not None:
            stmt = stmt.where(WorkspaceMember.role == role)
        return (await self._session.scalars(stmt)).all()

    async def count_members(
        self, workspace_id: uuid.UUID, *, role: WorkspaceRole | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.deleted_at.is_(None)
            )
        )
        if role is not None:
            stmt = stmt.where(WorkspaceMember.role == role)
        return (await self._session.scalar(stmt)) or 0

    async def remove_member(self, member_id: uuid.UUID) -> None:
        await self._session.execute(
            update(WorkspaceMember)
            .where(WorkspaceMember.id == member_id)
            .values(deleted_at=datetime.now(UTC))
        )

    async def list_memberships_by_user(self, user_id: uuid.UUID) -> Sequence[WorkspaceMember]:
        """Carrega o `Workspace` junto (`selectinload`) — usado por `GET /users/me`
        para compor `{ user, workspaces: [{ id, name, slug, role }] }` sem N+1.
        """
        stmt = (
            select(WorkspaceMember)
            .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id, WorkspaceMember.deleted_at.is_(None))
            .where(Workspace.deleted_at.is_(None))
            .options(selectinload(WorkspaceMember.workspace))
        )
        return (await self._session.scalars(stmt)).all()

    async def record_activity(self, entry: WorkspaceActivityLog) -> WorkspaceActivityLog:
        self._session.add(entry)
        await self._session.flush()
        return entry


class InvitationRepositoryProtocol(Protocol):
    async def create(self, invitation: Invitation) -> Invitation: ...
    async def get_by_id(
        self, workspace_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> Invitation | None: ...
    async def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...
    async def get_pending_by_email(
        self, workspace_id: uuid.UUID, email: str
    ) -> Invitation | None: ...
    async def list_by_workspace(
        self, workspace_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Invitation]: ...
    async def count_by_workspace(self, workspace_id: uuid.UUID) -> int: ...
    async def cancel(self, invitation_id: uuid.UUID) -> None: ...
    async def mark_accepted(self, invitation_id: uuid.UUID) -> None: ...


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, invitation: Invitation) -> Invitation:
        self._session.add(invitation)
        await self._session.flush()
        return invitation

    async def get_by_id(
        self, workspace_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.workspace_id == workspace_id,
            Invitation.deleted_at.is_(None),
        )
        result: Invitation | None = await self._session.scalar(stmt)
        return result

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

    async def list_by_workspace(
        self, workspace_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> Sequence[Invitation]:
        stmt = (
            select(Invitation)
            .where(Invitation.workspace_id == workspace_id, Invitation.deleted_at.is_(None))
            .order_by(Invitation.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_workspace(self, workspace_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Invitation)
            .where(Invitation.workspace_id == workspace_id, Invitation.deleted_at.is_(None))
        )
        return (await self._session.scalar(stmt)) or 0

    async def cancel(self, invitation_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(deleted_at=datetime.now(UTC))
        )

    async def mark_accepted(self, invitation_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(accepted_at=datetime.now(UTC))
        )
