import uuid

import pytest
from src.core.authorization import LOCKED_PERMISSIONS, ROLE_PERMISSIONS
from src.core.permissions import Permission
from src.features.permissions.exceptions import CannotOverrideOwnerRoleError, LockedPermissionError
from src.features.permissions.service import (
    OVERRIDABLE_PERMISSIONS,
    OVERRIDABLE_ROLES,
    PermissionOverrideService,
)
from src.features.workspaces.models import WorkspaceRole

from tests.unit.features.permissions.fakes import FakePermissionOverrideRepository


@pytest.fixture
def repo() -> FakePermissionOverrideRepository:
    return FakePermissionOverrideRepository()


@pytest.fixture
def service(repo: FakePermissionOverrideRepository) -> PermissionOverrideService:
    return PermissionOverrideService(repo)


class TestListMatrix:
    async def test_matrix_covers_every_overridable_role_and_permission(
        self, service: PermissionOverrideService
    ) -> None:
        entries = await service.list_matrix(uuid.uuid4())

        assert len(entries) == len(OVERRIDABLE_ROLES) * len(OVERRIDABLE_PERMISSIONS)

    async def test_matrix_never_includes_owner_or_locked_permissions(
        self, service: PermissionOverrideService
    ) -> None:
        entries = await service.list_matrix(uuid.uuid4())

        assert all(entry.role != WorkspaceRole.OWNER for entry in entries)
        assert all(entry.permission not in LOCKED_PERMISSIONS for entry in entries)

    async def test_no_overrides_means_effective_equals_default(
        self, service: PermissionOverrideService
    ) -> None:
        entries = await service.list_matrix(uuid.uuid4())

        for entry in entries:
            assert entry.effective == entry.default
            assert entry.is_override is False
            assert entry.default == (entry.permission in ROLE_PERMISSIONS[entry.role])


class TestSetOverride:
    async def test_granting_a_permission_the_role_lacks_by_default(
        self, service: PermissionOverrideService
    ) -> None:
        workspace_id = uuid.uuid4()
        assert Permission.ISSUE_CREATE not in ROLE_PERMISSIONS[WorkspaceRole.GUEST]

        entries = await service.set_override(
            workspace_id, WorkspaceRole.GUEST, Permission.ISSUE_CREATE, granted=True
        )

        entry = next(
            e
            for e in entries
            if e.role == WorkspaceRole.GUEST and e.permission == Permission.ISSUE_CREATE
        )
        assert entry.effective is True
        assert entry.is_override is True
        assert entry.default is False

    async def test_revoking_a_permission_the_role_has_by_default(
        self, service: PermissionOverrideService
    ) -> None:
        workspace_id = uuid.uuid4()
        assert Permission.ISSUE_CREATE in ROLE_PERMISSIONS[WorkspaceRole.MEMBER]

        entries = await service.set_override(
            workspace_id, WorkspaceRole.MEMBER, Permission.ISSUE_CREATE, granted=False
        )

        entry = next(
            e
            for e in entries
            if e.role == WorkspaceRole.MEMBER and e.permission == Permission.ISSUE_CREATE
        )
        assert entry.effective is False
        assert entry.is_override is True

    async def test_setting_back_to_default_removes_the_override(
        self, service: PermissionOverrideService, repo: FakePermissionOverrideRepository
    ) -> None:
        workspace_id = uuid.uuid4()
        await service.set_override(
            workspace_id, WorkspaceRole.MEMBER, Permission.ISSUE_CREATE, granted=False
        )
        assert len(repo.overrides) == 1

        entries = await service.set_override(
            workspace_id, WorkspaceRole.MEMBER, Permission.ISSUE_CREATE, granted=True
        )

        assert len(repo.overrides) == 0
        entry = next(
            e
            for e in entries
            if e.role == WorkspaceRole.MEMBER and e.permission == Permission.ISSUE_CREATE
        )
        assert entry.is_override is False

    async def test_overriding_the_same_permission_twice_updates_in_place(
        self, service: PermissionOverrideService, repo: FakePermissionOverrideRepository
    ) -> None:
        workspace_id = uuid.uuid4()
        await service.set_override(
            workspace_id, WorkspaceRole.GUEST, Permission.ISSUE_CREATE, granted=True
        )
        await service.set_override(
            workspace_id, WorkspaceRole.GUEST, Permission.ISSUE_UPDATE, granted=True
        )

        assert len(repo.overrides) == 2

    async def test_cannot_override_owner_role(self, service: PermissionOverrideService) -> None:
        with pytest.raises(CannotOverrideOwnerRoleError):
            await service.set_override(
                uuid.uuid4(), WorkspaceRole.OWNER, Permission.ISSUE_CREATE, granted=False
            )

    @pytest.mark.parametrize("permission", sorted(LOCKED_PERMISSIONS, key=str))
    async def test_cannot_override_locked_permission(
        self, service: PermissionOverrideService, permission: Permission
    ) -> None:
        with pytest.raises(LockedPermissionError):
            await service.set_override(uuid.uuid4(), WorkspaceRole.ADMIN, permission, granted=True)

    async def test_overrides_are_scoped_per_workspace(
        self, service: PermissionOverrideService
    ) -> None:
        workspace_a = uuid.uuid4()
        workspace_b = uuid.uuid4()

        await service.set_override(
            workspace_a, WorkspaceRole.GUEST, Permission.ISSUE_CREATE, granted=True
        )
        entries_b = await service.list_matrix(workspace_b)

        entry_b = next(
            e
            for e in entries_b
            if e.role == WorkspaceRole.GUEST and e.permission == Permission.ISSUE_CREATE
        )
        assert entry_b.is_override is False
