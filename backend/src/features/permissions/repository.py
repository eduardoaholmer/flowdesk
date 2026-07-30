import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.permissions import Permission
from src.features.permissions.models import PermissionOverride
from src.features.workspaces.models import WorkspaceRole


class PermissionOverrideRepositoryProtocol(Protocol):
    async def get(
        self, workspace_id: uuid.UUID, role: WorkspaceRole, permission: Permission
    ) -> PermissionOverride | None: ...
    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[PermissionOverride]: ...
    async def get_role_overrides(
        self, workspace_id: uuid.UUID, role: WorkspaceRole
    ) -> tuple[frozenset[Permission], frozenset[Permission]]: ...
    async def create(self, override: PermissionOverride) -> PermissionOverride: ...
    async def update(self, override: PermissionOverride) -> PermissionOverride: ...
    async def delete(self, override_id: uuid.UUID) -> None: ...


class PermissionOverrideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, workspace_id: uuid.UUID, role: WorkspaceRole, permission: Permission
    ) -> PermissionOverride | None:
        stmt = select(PermissionOverride).where(
            PermissionOverride.workspace_id == workspace_id,
            PermissionOverride.role == role,
            PermissionOverride.permission == permission,
        )
        result: PermissionOverride | None = await self._session.scalar(stmt)
        return result

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[PermissionOverride]:
        stmt = select(PermissionOverride).where(PermissionOverride.workspace_id == workspace_id)
        return (await self._session.scalars(stmt)).all()

    async def get_role_overrides(
        self, workspace_id: uuid.UUID, role: WorkspaceRole
    ) -> tuple[frozenset[Permission], frozenset[Permission]]:
        """Usado por `core/authorization.py::get_workspace_context` em toda
        requisição autenticada — restrito ao papel do chamador (nunca precisa
        da matriz inteira do workspace, só a própria linha)."""
        stmt = select(PermissionOverride.permission, PermissionOverride.granted).where(
            PermissionOverride.workspace_id == workspace_id, PermissionOverride.role == role
        )
        granted: set[Permission] = set()
        revoked: set[Permission] = set()
        for permission, is_granted in (await self._session.execute(stmt)).all():
            (granted if is_granted else revoked).add(permission)
        return frozenset(granted), frozenset(revoked)

    async def create(self, override: PermissionOverride) -> PermissionOverride:
        self._session.add(override)
        await self._session.flush()
        return override

    async def update(self, override: PermissionOverride) -> PermissionOverride:
        await self._session.flush()
        return override

    async def delete(self, override_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(PermissionOverride).where(PermissionOverride.id == override_id)
        )
