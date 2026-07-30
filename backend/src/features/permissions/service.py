import uuid

from src.core.authorization import LOCKED_PERMISSIONS, ROLE_PERMISSIONS
from src.core.permissions import Permission
from src.features.permissions.exceptions import CannotOverrideOwnerRoleError, LockedPermissionError
from src.features.permissions.models import PermissionOverride
from src.features.permissions.repository import PermissionOverrideRepositoryProtocol
from src.features.permissions.schemas import PermissionMatrixEntryResponse
from src.features.workspaces.models import WorkspaceRole

#: Papéis que aceitam customização — OWNER sempre tem `frozenset(Permission)`
#: inteiro, nunca aparece na matriz nem pode receber override (Sprint 9.3,
#: ADR-058, meio-termo decidido: RBAC fixo continua fixo para o dono).
OVERRIDABLE_ROLES: tuple[WorkspaceRole, ...] = (
    WorkspaceRole.ADMIN,
    WorkspaceRole.MEMBER,
    WorkspaceRole.GUEST,
)

#: Permissões exibidas/editáveis na matriz — todas exceto as exclusivas do
#: OWNER (`LOCKED_PERMISSIONS`), que nunca aparecem como linha da tabela.
OVERRIDABLE_PERMISSIONS: tuple[Permission, ...] = tuple(
    permission for permission in Permission if permission not in LOCKED_PERMISSIONS
)


class PermissionOverrideService:
    def __init__(self, repo: PermissionOverrideRepositoryProtocol) -> None:
        self._repo = repo

    async def list_matrix(self, workspace_id: uuid.UUID) -> list[PermissionMatrixEntryResponse]:
        existing = await self._repo.list_for_workspace(workspace_id)
        overrides = {
            (override.role, override.permission): override.granted for override in existing
        }

        entries: list[PermissionMatrixEntryResponse] = []
        for role in OVERRIDABLE_ROLES:
            for permission in OVERRIDABLE_PERMISSIONS:
                default = permission in ROLE_PERMISSIONS[role]
                override = overrides.get((role, permission))
                entries.append(
                    PermissionMatrixEntryResponse(
                        permission=permission,
                        role=role,
                        default=default,
                        effective=default if override is None else override,
                        is_override=override is not None,
                    )
                )
        return entries

    async def set_override(
        self, workspace_id: uuid.UUID, role: WorkspaceRole, permission: Permission, granted: bool
    ) -> list[PermissionMatrixEntryResponse]:
        if role == WorkspaceRole.OWNER:
            raise CannotOverrideOwnerRoleError()
        if permission in LOCKED_PERMISSIONS:
            raise LockedPermissionError()

        default = permission in ROLE_PERMISSIONS[role]
        existing = await self._repo.get(workspace_id, role, permission)

        if granted == default:
            # Volta a bater com o padrão — remove o override em vez de guardar
            # uma linha redundante (a tabela só existe para os desvios reais).
            if existing is not None:
                await self._repo.delete(existing.id)
        elif existing is not None:
            existing.granted = granted
            await self._repo.update(existing)
        else:
            await self._repo.create(
                PermissionOverride(
                    workspace_id=workspace_id, role=role, permission=permission, granted=granted
                )
            )

        return await self.list_matrix(workspace_id)
