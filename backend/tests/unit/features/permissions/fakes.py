import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.core.permissions import Permission
from src.features.permissions.models import PermissionOverride
from src.features.workspaces.models import WorkspaceRole
from uuid6 import uuid7


class FakePermissionOverrideRepository:
    """Implementa `PermissionOverrideRepositoryProtocol` em memória — mesmo
    racional de `tests/unit/features/workflow_states/fakes.py`."""

    def __init__(self) -> None:
        self.overrides: dict[uuid.UUID, PermissionOverride] = {}

    async def get(
        self, workspace_id: uuid.UUID, role: WorkspaceRole, permission: Permission
    ) -> PermissionOverride | None:
        for override in self.overrides.values():
            if (
                override.workspace_id == workspace_id
                and override.role == role
                and override.permission == permission
            ):
                return override
        return None

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[PermissionOverride]:
        return [
            override
            for override in self.overrides.values()
            if override.workspace_id == workspace_id
        ]

    async def get_role_overrides(
        self, workspace_id: uuid.UUID, role: WorkspaceRole
    ) -> tuple[frozenset[Permission], frozenset[Permission]]:
        granted: set[Permission] = set()
        revoked: set[Permission] = set()
        for override in self.overrides.values():
            if override.workspace_id == workspace_id and override.role == role:
                (granted if override.granted else revoked).add(override.permission)
        return frozenset(granted), frozenset(revoked)

    async def create(self, override: PermissionOverride) -> PermissionOverride:
        if override.id is None:
            override.id = uuid7()
        now = datetime.now(UTC)
        override.created_at = override.created_at or now
        override.updated_at = override.updated_at or now
        self.overrides[override.id] = override
        return override

    async def update(self, override: PermissionOverride) -> PermissionOverride:
        override.updated_at = datetime.now(UTC)
        return override

    async def delete(self, override_id: uuid.UUID) -> None:
        self.overrides.pop(override_id, None)
