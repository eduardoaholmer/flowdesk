import uuid
from datetime import UTC, datetime, timedelta

import pytest
from src.core.authorization import PermissionService
from src.core.config import Settings
from src.core.security import CurrentUser
from src.features.auth.models import User
from src.features.workspaces.exceptions import (
    AlreadyMemberError,
    InvitationAlreadyPendingError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
)
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole
from src.features.workspaces.schemas import InvitationCreateRequest, WorkspaceCreateRequest
from src.features.workspaces.service import InvitationService, WorkspaceService

from tests.unit.features.auth.fakes import FakeUserRepository
from tests.unit.features.workspaces.fakes import FakeInvitationRepository, FakeWorkspaceRepository

# Autorização (quem pode convidar/cancelar) não é mais uma regra deste service
# — o router já resolveu `Depends(require_permission(WORKSPACE_INVITE))` antes
# dele ser chamado (Sprint 5, `core/authorization.py`). Os cenários de
# OWNER/ADMIN podem, MEMBER/GUEST/não-membro não podem, vivem agora em
# `tests/unit/core/test_authorization.py` (matriz pura) e em
# `tests/contract/test_authorization.py` (fim a fim, via HTTP).


@pytest.fixture
def workspace_repo() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def invitation_repo() -> FakeInvitationRepository:
    return FakeInvitationRepository()


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def workspace_service(workspace_repo: FakeWorkspaceRepository) -> WorkspaceService:
    return WorkspaceService(workspace_repo, PermissionService())


@pytest.fixture
def service(
    invitation_repo: FakeInvitationRepository,
    workspace_repo: FakeWorkspaceRepository,
    user_repo: FakeUserRepository,
    settings: Settings,
) -> InvitationService:
    return InvitationService(invitation_repo, workspace_repo, user_repo, settings)


def _user(email: str = "ada@example.com") -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email=email, name="Ada Lovelace")


async def test_create_issues_token_and_records_activity(
    service: InvitationService,
    workspace_service: WorkspaceService,
    workspace_repo: FakeWorkspaceRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))

    issued = await service.create(
        owner,
        workspace.id,
        InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER),
    )

    assert issued.token
    assert issued.invitation.email == "invitee@example.com"
    assert any(entry.action == "invitation.sent" for entry in workspace_repo.activity_log)


async def test_create_rejects_duplicate_pending_invitation(
    service: InvitationService, workspace_service: WorkspaceService
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    payload = InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER)
    await service.create(owner, workspace.id, payload)

    with pytest.raises(InvitationAlreadyPendingError):
        await service.create(owner, workspace.id, payload)


async def test_create_rejects_email_already_member(
    service: InvitationService,
    workspace_service: WorkspaceService,
    workspace_repo: FakeWorkspaceRepository,
    user_repo: FakeUserRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))

    existing_user = await user_repo.create(
        User(name="Grace", email="grace@example.com", password_hash="hash")
    )
    await workspace_repo.add_member(
        WorkspaceMember(
            workspace_id=workspace.id, user_id=existing_user.id, role=WorkspaceRole.MEMBER
        )
    )

    with pytest.raises(AlreadyMemberError):
        await service.create(
            owner,
            workspace.id,
            InvitationCreateRequest(email="grace@example.com", role=WorkspaceRole.MEMBER),
        )


async def test_accept_creates_membership(
    service: InvitationService,
    workspace_service: WorkspaceService,
    user_repo: FakeUserRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    issued = await service.create(
        owner,
        workspace.id,
        InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER),
    )
    invitee = _user("invitee@example.com")
    # `accept` assume que `current_user` já foi resolvido por `get_current_user`
    # contra o banco real — o fake precisa espelhar essa garantia manualmente.
    await user_repo.create(
        User(id=invitee.id, name=invitee.name, email=invitee.email, password_hash="hash")
    )

    member = await service.accept(invitee, issued.token)

    assert member.workspace_id == workspace.id
    assert member.role == WorkspaceRole.MEMBER


async def test_accept_rejects_unknown_token(service: InvitationService) -> None:
    with pytest.raises(InvitationNotFoundError):
        await service.accept(_user(), "not-a-real-token")


async def test_accept_rejects_expired_invitation(
    service: InvitationService,
    workspace_service: WorkspaceService,
    invitation_repo: FakeInvitationRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    issued = await service.create(
        owner,
        workspace.id,
        InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER),
    )
    issued.invitation.expires_at = datetime.now(UTC) - timedelta(days=1)

    with pytest.raises(InvitationExpiredError):
        await service.accept(_user("invitee@example.com"), issued.token)


async def test_accept_rejects_mismatched_email(
    service: InvitationService, workspace_service: WorkspaceService
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    issued = await service.create(
        owner,
        workspace.id,
        InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER),
    )

    with pytest.raises(InvitationEmailMismatchError):
        await service.accept(_user("someone-else@example.com"), issued.token)


async def test_accept_rejects_when_already_member(
    service: InvitationService,
    workspace_service: WorkspaceService,
    workspace_repo: FakeWorkspaceRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    invitee = _user("invitee@example.com")
    issued = await service.create(
        owner, workspace.id, InvitationCreateRequest(email=invitee.email, role=WorkspaceRole.MEMBER)
    )
    await workspace_repo.add_member(
        WorkspaceMember(workspace_id=workspace.id, user_id=invitee.id, role=WorkspaceRole.GUEST)
    )

    with pytest.raises(AlreadyMemberError):
        await service.accept(invitee, issued.token)


async def test_cancel_invitation(
    service: InvitationService,
    workspace_service: WorkspaceService,
    invitation_repo: FakeInvitationRepository,
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))
    issued = await service.create(
        owner,
        workspace.id,
        InvitationCreateRequest(email="invitee@example.com", role=WorkspaceRole.MEMBER),
    )

    await service.cancel(workspace.id, issued.invitation.id)

    assert await invitation_repo.get_by_id(workspace.id, issued.invitation.id) is None


async def test_cancel_rejects_unknown_invitation(
    service: InvitationService, workspace_service: WorkspaceService
) -> None:
    owner = _user()
    workspace = await workspace_service.create(owner, WorkspaceCreateRequest(name="Acme"))

    with pytest.raises(InvitationNotFoundError):
        await service.cancel(workspace.id, uuid.uuid4())
