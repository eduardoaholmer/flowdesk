import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.models import User
from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory
from src.features.workflow_states.repository import WorkflowStateRepository
from src.features.workspaces.models import Workspace
from src.features.workspaces.repository import WorkspaceRepository


async def test_only_one_default_workflow_state_per_workspace(
    db_session: AsyncSession, workflow_state_repo: WorkflowStateRepository, workspace: Workspace
) -> None:
    await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace.id,
            name="Backlog",
            category=WorkflowStateCategory.BACKLOG,
            position=0,
            is_default=True,
        )
    )
    another_default = WorkflowState(
        workspace_id=workspace.id,
        name="Doing",
        category=WorkflowStateCategory.STARTED,
        position=1,
        is_default=True,
    )
    db_session.add(another_default)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_name_unique_per_workspace_while_active(
    workflow_state_repo: WorkflowStateRepository, workspace: Workspace
) -> None:
    await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace.id,
            name="Backlog",
            category=WorkflowStateCategory.BACKLOG,
            position=0,
            is_default=True,
        )
    )

    with pytest.raises(IntegrityError):
        await workflow_state_repo.create(
            WorkflowState(
                workspace_id=workspace.id,
                name="Backlog",
                category=WorkflowStateCategory.STARTED,
                position=1,
                is_default=False,
            )
        )


async def test_position_unique_per_workspace_while_active(
    workflow_state_repo: WorkflowStateRepository, workspace: Workspace
) -> None:
    await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace.id,
            name="Backlog",
            category=WorkflowStateCategory.BACKLOG,
            position=0,
            is_default=True,
        )
    )

    with pytest.raises(IntegrityError):
        await workflow_state_repo.create(
            WorkflowState(
                workspace_id=workspace.id,
                name="Doing",
                category=WorkflowStateCategory.STARTED,
                position=0,
                is_default=False,
            )
        )


async def test_name_free_again_in_a_different_workspace(
    db_session: AsyncSession,
    workflow_state_repo: WorkflowStateRepository,
    workspace: Workspace,
    user: User,
) -> None:
    """Mesma constraint, mas confirmando o outro lado — dois workspaces podem
    ter um status "Backlog" cada, já que o índice único é por `workspace_id`."""
    other_workspace_repo = WorkspaceRepository(db_session)
    other_workspace = await other_workspace_repo.create(
        Workspace(name="Other", slug="other-ws", owner_id=user.id)
    )

    await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace.id,
            name="Backlog",
            category=WorkflowStateCategory.BACKLOG,
            position=0,
            is_default=True,
        )
    )
    second = await workflow_state_repo.create(
        WorkflowState(
            workspace_id=other_workspace.id,
            name="Backlog",
            category=WorkflowStateCategory.BACKLOG,
            position=0,
            is_default=True,
        )
    )

    assert second.workspace_id == other_workspace.id
