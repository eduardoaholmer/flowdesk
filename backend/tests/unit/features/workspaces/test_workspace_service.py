import uuid

import pytest
from src.core.authorization import PermissionService
from src.core.exceptions import PermissionDeniedError
from src.core.security import CurrentUser
from src.features.workspaces.exceptions import (
    CannotLeaveAsSoleOwnerError,
    CannotManageOwnMembershipError,
    MemberNotFoundError,
    SlugTakenError,
    WorkspaceNotFoundError,
)
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole
from src.features.workspaces.schemas import WorkspaceCreateRequest, WorkspaceUpdateRequest
from src.features.workspaces.service import WorkspaceService

from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository

# Autorização por papel (quem pode `PATCH`/`DELETE` um workspace) não é mais
# checada por este service — o router resolve `Depends(require_permission(...))`
# antes de chamá-lo (Sprint 5, `core/authorization.py`). Esses cenários vivem
# agora em `tests/unit/core/test_authorization.py` (matriz pura) e em
# `tests/contract/test_authorization.py` (fim a fim, via HTTP). O que resta
# testável aqui é regra de negócio pura: geração de slug, registro de
# atividade, e a checagem contextual de gerenciamento de membro
# (`require_can_manage_member`), que só o service pode fazer porque depende de
# um recurso (o membro-alvo) já buscado.


@pytest.fixture
def workspace_repo() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def service(workspace_repo: FakeWorkspaceRepository) -> WorkspaceService:
    return WorkspaceService(workspace_repo, PermissionService())


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


async def test_create_makes_creator_owner(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()

    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme Inc"))

    member = await workspace_repo.get_member(workspace.id, owner.id)
    assert member is not None
    assert member.role == WorkspaceRole.OWNER
    assert workspace.owner_id == owner.id
    assert any(entry.action == "workspace.created" for entry in workspace_repo.activity_log)


async def test_create_generates_slug_when_not_provided(service: WorkspaceService) -> None:
    workspace = await service.create(_user(), WorkspaceCreateRequest(name="Acme Inc"))

    assert workspace.slug
    assert workspace.slug.startswith("acme-inc")


async def test_create_rejects_taken_slug(service: WorkspaceService) -> None:
    await service.create(_user(), WorkspaceCreateRequest(name="Acme", slug="acme"))

    with pytest.raises(SlugTakenError):
        await service.create(_user(), WorkspaceCreateRequest(name="Acme 2", slug="acme"))


async def test_list_for_user_returns_only_member_workspaces(service: WorkspaceService) -> None:
    owner_a = _user("a@example.com")
    owner_b = _user("b@example.com")
    await service.create(owner_a, WorkspaceCreateRequest(name="Workspace A"))
    await service.create(owner_b, WorkspaceCreateRequest(name="Workspace B"))

    workspaces, total = await service.list_for_user(owner_a, page=1, per_page=20)

    assert total == 1
    assert [w.name for w in workspaces] == ["Workspace A"]


async def test_get_raises_not_found_for_unknown_workspace(service: WorkspaceService) -> None:
    with pytest.raises(WorkspaceNotFoundError):
        await service.get(uuid.uuid4())


async def test_update_changes_fields_and_records_activity(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))

    updated = await service.update(
        owner, workspace.id, WorkspaceUpdateRequest(name="Acme Renamed", description="new desc")
    )

    assert updated.name == "Acme Renamed"
    assert updated.description == "new desc"
    assert any(entry.action == "workspace.updated" for entry in workspace_repo.activity_log)


async def test_update_rejects_taken_slug(service: WorkspaceService) -> None:
    owner = _user()
    await service.create(owner, WorkspaceCreateRequest(name="Other", slug="taken"))
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme", slug="acme"))

    with pytest.raises(SlugTakenError):
        await service.update(owner, workspace.id, WorkspaceUpdateRequest(slug="taken"))


async def test_delete_soft_deletes_workspace(service: WorkspaceService) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))

    await service.delete(owner, workspace.id)

    with pytest.raises(WorkspaceNotFoundError):
        await service.get(workspace.id)


async def test_leave_sole_owner_cannot_leave(service: WorkspaceService) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))

    with pytest.raises(CannotLeaveAsSoleOwnerError):
        await service.leave(owner, workspace.id)


async def test_leave_removes_membership_for_non_sole_owner(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    member_user = _user("member@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    await workspace_repo.add_member(
        WorkspaceMember(
            workspace_id=workspace.id, user_id=member_user.id, role=WorkspaceRole.MEMBER
        )
    )

    await service.leave(member_user, workspace.id)

    assert await workspace_repo.get_member(workspace.id, member_user.id) is None


async def test_leave_owner_succeeds_when_another_owner_remains(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    co_owner = _user("co-owner@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    await workspace_repo.add_member(
        WorkspaceMember(workspace_id=workspace.id, user_id=co_owner.id, role=WorkspaceRole.OWNER)
    )

    await service.leave(owner, workspace.id)

    assert await workspace_repo.get_member(workspace.id, owner.id) is None


async def test_leave_raises_not_found_for_non_member(service: WorkspaceService) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))

    with pytest.raises(WorkspaceNotFoundError):
        await service.leave(_user("outsider@example.com"), workspace.id)


async def test_update_member_role_changes_role_and_records_activity(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    member_user = _user("member@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    member = await workspace_repo.add_member(
        WorkspaceMember(
            workspace_id=workspace.id, user_id=member_user.id, role=WorkspaceRole.MEMBER
        )
    )

    updated = await service.update_member_role(
        owner, workspace.id, member.id, WorkspaceRole.ADMIN, WorkspaceRole.OWNER
    )

    assert updated.role == WorkspaceRole.ADMIN
    assert any(entry.action == "member.role_changed" for entry in workspace_repo.activity_log)


async def test_update_member_role_rejects_unknown_member(service: WorkspaceService) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))

    with pytest.raises(MemberNotFoundError):
        await service.update_member_role(
            owner, workspace.id, uuid.uuid4(), WorkspaceRole.ADMIN, WorkspaceRole.OWNER
        )


async def test_update_member_role_rejects_self_target(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    own_member = await workspace_repo.get_member(workspace.id, owner.id)
    assert own_member is not None

    with pytest.raises(CannotManageOwnMembershipError):
        await service.update_member_role(
            owner, workspace.id, own_member.id, WorkspaceRole.ADMIN, WorkspaceRole.OWNER
        )


async def test_update_member_role_admin_cannot_manage_owner(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    admin_user = _user("admin@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    owner_member = await workspace_repo.get_member(workspace.id, owner.id)
    assert owner_member is not None
    await workspace_repo.add_member(
        WorkspaceMember(workspace_id=workspace.id, user_id=admin_user.id, role=WorkspaceRole.ADMIN)
    )

    with pytest.raises(PermissionDeniedError):
        await service.update_member_role(
            admin_user, workspace.id, owner_member.id, WorkspaceRole.MEMBER, WorkspaceRole.ADMIN
        )


async def test_remove_member_removes_and_records_activity(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    member_user = _user("member@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    member = await workspace_repo.add_member(
        WorkspaceMember(
            workspace_id=workspace.id, user_id=member_user.id, role=WorkspaceRole.MEMBER
        )
    )

    await service.remove_member(owner, workspace.id, member.id, WorkspaceRole.OWNER)

    assert await workspace_repo.get_member(workspace.id, member_user.id) is None
    assert any(entry.action == "member.removed" for entry in workspace_repo.activity_log)


async def test_remove_member_admin_cannot_remove_owner(
    service: WorkspaceService, workspace_repo: FakeWorkspaceRepository
) -> None:
    owner = _user()
    admin_user = _user("admin@example.com")
    workspace = await service.create(owner, WorkspaceCreateRequest(name="Acme"))
    owner_member = await workspace_repo.get_member(workspace.id, owner.id)
    assert owner_member is not None
    await workspace_repo.add_member(
        WorkspaceMember(workspace_id=workspace.id, user_id=admin_user.id, role=WorkspaceRole.ADMIN)
    )

    with pytest.raises(PermissionDeniedError):
        await service.remove_member(admin_user, workspace.id, owner_member.id, WorkspaceRole.ADMIN)
