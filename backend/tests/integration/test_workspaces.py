import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.features.auth.models import User
from src.features.workspaces.models import Invitation, Workspace, WorkspaceMember, WorkspaceRole
from src.features.workspaces.repository import InvitationRepository, WorkspaceRepository


async def test_workspace_membership_relationship_loads(
    db_session: AsyncSession, workspace: Workspace, user: User
) -> None:
    stmt = (
        select(Workspace)
        .options(selectinload(Workspace.members))
        .where(Workspace.id == workspace.id)
    )
    loaded = await db_session.scalar(stmt)

    assert loaded is not None
    assert len(loaded.members) == 1
    assert loaded.members[0].user_id == user.id
    assert loaded.members[0].role == WorkspaceRole.OWNER


async def test_list_by_user_returns_workspace(
    workspace_repo: WorkspaceRepository, workspace: Workspace, user: User
) -> None:
    workspaces = await workspace_repo.list_by_user(user.id)

    assert [w.id for w in workspaces] == [workspace.id]


async def test_slug_unique_while_active(
    workspace_repo: WorkspaceRepository, workspace: Workspace, user: User
) -> None:
    with pytest.raises(IntegrityError):
        await workspace_repo.create(Workspace(name="Acme 2", slug=workspace.slug, owner_id=user.id))


async def test_member_unique_per_workspace(
    workspace_repo: WorkspaceRepository, workspace: Workspace, user: User
) -> None:
    with pytest.raises(IntegrityError):
        await workspace_repo.add_member(
            WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.MEMBER)
        )


async def test_pending_invitation_unique_per_email(
    invitation_repo: InvitationRepository, workspace: Workspace, user: User
) -> None:
    email = "invitee@example.com"
    await invitation_repo.create(
        Invitation(
            workspace_id=workspace.id,
            email=email,
            role=WorkspaceRole.MEMBER,
            token_hash=f"hash-{uuid.uuid4()}",
            invited_by_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
    )

    with pytest.raises(IntegrityError):
        await invitation_repo.create(
            Invitation(
                workspace_id=workspace.id,
                email=email,
                role=WorkspaceRole.ADMIN,
                token_hash=f"hash-{uuid.uuid4()}",
                invited_by_id=user.id,
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
        )
