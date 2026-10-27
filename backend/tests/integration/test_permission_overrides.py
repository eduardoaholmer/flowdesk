import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.permissions import Permission
from src.features.permissions.models import PermissionOverride
from src.features.permissions.repository import PermissionOverrideRepository
from src.features.workspaces.models import Workspace, WorkspaceRole


async def test_unique_per_workspace_role_permission(
    db_session: AsyncSession,
    permission_override_repo: PermissionOverrideRepository,
    workspace: Workspace,
) -> None:
    await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.MEMBER,
            permission=Permission.ISSUE_CREATE,
            granted=False,
        )
    )
    duplicate = PermissionOverride(
        workspace_id=workspace.id,
        role=WorkspaceRole.MEMBER,
        permission=Permission.ISSUE_CREATE,
        granted=True,
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_same_permission_free_again_for_a_different_role(
    permission_override_repo: PermissionOverrideRepository, workspace: Workspace
) -> None:
    """Mesma constraint, lado oposto — o índice único é (workspace_id, role,
    permission), então o mesmo par (workspace, permissão) aceita uma linha por
    papel."""
    await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.MEMBER,
            permission=Permission.ISSUE_CREATE,
            granted=False,
        )
    )
    second = await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.GUEST,
            permission=Permission.ISSUE_CREATE,
            granted=True,
        )
    )

    assert second.role == WorkspaceRole.GUEST


async def test_get_role_overrides_splits_granted_and_revoked(
    permission_override_repo: PermissionOverrideRepository, workspace: Workspace
) -> None:
    await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.GUEST,
            permission=Permission.ISSUE_CREATE,
            granted=True,
        )
    )
    await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.GUEST,
            permission=Permission.LABEL_READ,
            granted=False,
        )
    )

    granted, revoked = await permission_override_repo.get_role_overrides(
        workspace.id, WorkspaceRole.GUEST
    )

    assert granted == frozenset({Permission.ISSUE_CREATE})
    assert revoked == frozenset({Permission.LABEL_READ})


async def test_delete_resets_to_default(
    permission_override_repo: PermissionOverrideRepository, workspace: Workspace
) -> None:
    override = await permission_override_repo.create(
        PermissionOverride(
            workspace_id=workspace.id,
            role=WorkspaceRole.GUEST,
            permission=Permission.ISSUE_CREATE,
            granted=True,
        )
    )

    await permission_override_repo.delete(override.id)

    granted, revoked = await permission_override_repo.get_role_overrides(
        workspace.id, WorkspaceRole.GUEST
    )
    assert granted == frozenset()
    assert revoked == frozenset()
