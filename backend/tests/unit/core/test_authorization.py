import uuid

import pytest
from src.core.authorization import (
    OWNERSHIP_OVERRIDE_PERMISSIONS,
    ROLE_PERMISSIONS,
    PermissionService,
)
from src.core.exceptions import PermissionDeniedError
from src.core.permissions import Permission
from src.features.workspaces.exceptions import CannotManageOwnerError
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole


def _member(role: WorkspaceRole, *, user_id: uuid.UUID | None = None) -> WorkspaceMember:
    return WorkspaceMember(
        workspace_id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        role=role,
    )


@pytest.fixture
def permission_service() -> PermissionService:
    return PermissionService()


class TestRolePermissionsMatrix:
    def test_owner_has_every_permission(self) -> None:
        assert ROLE_PERMISSIONS[WorkspaceRole.OWNER] == frozenset(Permission)

    def test_admin_has_every_permission_except_workspace_delete(self) -> None:
        admin_permissions = ROLE_PERMISSIONS[WorkspaceRole.ADMIN]

        assert Permission.WORKSPACE_DELETE not in admin_permissions
        assert admin_permissions == frozenset(Permission) - {Permission.WORKSPACE_DELETE}

    def test_member_cannot_manage_workspace_or_members(self) -> None:
        member_permissions = ROLE_PERMISSIONS[WorkspaceRole.MEMBER]

        assert Permission.WORKSPACE_UPDATE not in member_permissions
        assert Permission.WORKSPACE_DELETE not in member_permissions
        assert Permission.WORKSPACE_INVITE not in member_permissions
        assert Permission.MEMBER_REMOVE not in member_permissions
        assert Permission.MEMBER_UPDATE_ROLE not in member_permissions

    def test_member_can_work_with_issues_and_comments(self) -> None:
        member_permissions = ROLE_PERMISSIONS[WorkspaceRole.MEMBER]

        assert Permission.ISSUE_CREATE in member_permissions
        assert Permission.ISSUE_UPDATE in member_permissions
        assert Permission.COMMENT_CREATE in member_permissions
        assert Permission.LABEL_CREATE in member_permissions

    def test_guest_is_read_only_plus_comment(self) -> None:
        guest_permissions = ROLE_PERMISSIONS[WorkspaceRole.GUEST]

        assert guest_permissions == frozenset(
            {
                Permission.WORKSPACE_VIEW,
                Permission.PROJECT_READ,
                Permission.ISSUE_READ,
                Permission.COMMENT_CREATE,
            }
        )

    def test_every_role_is_covered(self) -> None:
        assert set(ROLE_PERMISSIONS.keys()) == set(WorkspaceRole)


class TestPermissionServiceCan:
    def test_owner_can_delete_workspace(self, permission_service: PermissionService) -> None:
        member = _member(WorkspaceRole.OWNER)

        assert permission_service.can(member=member, permission=Permission.WORKSPACE_DELETE)

    def test_admin_cannot_delete_workspace(self, permission_service: PermissionService) -> None:
        member = _member(WorkspaceRole.ADMIN)

        assert not permission_service.can(member=member, permission=Permission.WORKSPACE_DELETE)

    def test_member_cannot_update_workspace(self, permission_service: PermissionService) -> None:
        member = _member(WorkspaceRole.MEMBER)

        assert not permission_service.can(member=member, permission=Permission.WORKSPACE_UPDATE)

    def test_guest_cannot_create_issue(self, permission_service: PermissionService) -> None:
        member = _member(WorkspaceRole.GUEST)

        assert not permission_service.can(member=member, permission=Permission.ISSUE_CREATE)

    @pytest.mark.parametrize("permission", sorted(OWNERSHIP_OVERRIDE_PERMISSIONS, key=str))
    def test_ownership_override_grants_permission_to_resource_owner(
        self, permission_service: PermissionService, permission: Permission
    ) -> None:
        user_id = uuid.uuid4()
        member = _member(WorkspaceRole.GUEST, user_id=user_id)

        assert permission_service.can(
            member=member, permission=permission, resource_owner_id=user_id
        )

    @pytest.mark.parametrize("permission", sorted(OWNERSHIP_OVERRIDE_PERMISSIONS, key=str))
    def test_ownership_override_does_not_grant_to_non_owner(
        self, permission_service: PermissionService, permission: Permission
    ) -> None:
        member = _member(WorkspaceRole.GUEST)

        assert not permission_service.can(
            member=member, permission=permission, resource_owner_id=uuid.uuid4()
        )

    def test_ownership_override_does_not_apply_to_permissions_outside_the_set(
        self, permission_service: PermissionService
    ) -> None:
        user_id = uuid.uuid4()
        member = _member(WorkspaceRole.GUEST, user_id=user_id)

        assert not permission_service.can(
            member=member, permission=Permission.ISSUE_CREATE, resource_owner_id=user_id
        )


class TestPermissionServiceRequire:
    def test_require_passes_silently_when_allowed(
        self, permission_service: PermissionService
    ) -> None:
        member = _member(WorkspaceRole.OWNER)

        permission_service.require(member=member, permission=Permission.WORKSPACE_DELETE)

    def test_require_raises_permission_denied_when_disallowed(
        self, permission_service: PermissionService
    ) -> None:
        member = _member(WorkspaceRole.MEMBER)

        with pytest.raises(PermissionDeniedError):
            permission_service.require(member=member, permission=Permission.WORKSPACE_DELETE)


class TestCanManageMember:
    @pytest.mark.parametrize(
        "target_role",
        [WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER, WorkspaceRole.GUEST],
    )
    def test_owner_can_manage_anyone(
        self, permission_service: PermissionService, target_role: WorkspaceRole
    ) -> None:
        assert permission_service.can_manage_member(
            actor_role=WorkspaceRole.OWNER, target_role=target_role
        )

    def test_admin_cannot_manage_owner(self, permission_service: PermissionService) -> None:
        assert not permission_service.can_manage_member(
            actor_role=WorkspaceRole.ADMIN, target_role=WorkspaceRole.OWNER
        )

    @pytest.mark.parametrize(
        "target_role", [WorkspaceRole.ADMIN, WorkspaceRole.MEMBER, WorkspaceRole.GUEST]
    )
    def test_admin_can_manage_non_owner(
        self, permission_service: PermissionService, target_role: WorkspaceRole
    ) -> None:
        assert permission_service.can_manage_member(
            actor_role=WorkspaceRole.ADMIN, target_role=target_role
        )

    @pytest.mark.parametrize("actor_role", [WorkspaceRole.MEMBER, WorkspaceRole.GUEST])
    def test_member_and_guest_cannot_manage_anyone(
        self, permission_service: PermissionService, actor_role: WorkspaceRole
    ) -> None:
        assert not permission_service.can_manage_member(
            actor_role=actor_role, target_role=WorkspaceRole.MEMBER
        )

    def test_require_can_manage_member_raises_cannot_manage_owner(
        self, permission_service: PermissionService
    ) -> None:
        with pytest.raises(CannotManageOwnerError):
            permission_service.require_can_manage_member(
                actor_role=WorkspaceRole.ADMIN, target_role=WorkspaceRole.OWNER
            )
