import uuid

from fastapi import APIRouter, Depends, Query, status

from src.core.authorization import require_permission
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.features.workflow_states.dependencies import get_workflow_state_service
from src.features.workflow_states.schemas import (
    WorkflowStateCreateRequest,
    WorkflowStateReorderRequest,
    WorkflowStateResponse,
    WorkflowStateUpdateRequest,
)
from src.features.workflow_states.service import WorkflowStateService
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/workflow-states", tags=["workflow-states"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[WorkflowStateResponse]
)
async def create_workflow_state(
    workspace_id: uuid.UUID,
    payload: WorkflowStateCreateRequest,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKFLOW_STATE_MANAGE)),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> DataEnvelope[WorkflowStateResponse]:
    view = await service.create(workspace_id, payload)
    return DataEnvelope(data=WorkflowStateResponse.from_view(view))


@router.get("", response_model=DataEnvelope[list[WorkflowStateResponse]])
async def list_workflow_states(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKFLOW_STATE_READ)),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> DataEnvelope[list[WorkflowStateResponse]]:
    views = await service.list_for_workspace(workspace_id)
    return DataEnvelope(data=[WorkflowStateResponse.from_view(view) for view in views])


@router.post("/reorder", response_model=DataEnvelope[list[WorkflowStateResponse]])
async def reorder_workflow_states(
    workspace_id: uuid.UUID,
    payload: WorkflowStateReorderRequest,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKFLOW_STATE_MANAGE)),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> DataEnvelope[list[WorkflowStateResponse]]:
    views = await service.reorder(workspace_id, payload)
    return DataEnvelope(data=[WorkflowStateResponse.from_view(view) for view in views])


@router.patch("/{state_id}", response_model=DataEnvelope[WorkflowStateResponse])
async def update_workflow_state(
    workspace_id: uuid.UUID,
    state_id: uuid.UUID,
    payload: WorkflowStateUpdateRequest,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKFLOW_STATE_MANAGE)),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> DataEnvelope[WorkflowStateResponse]:
    view = await service.update(workspace_id, state_id, payload)
    return DataEnvelope(data=WorkflowStateResponse.from_view(view))


@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_state(
    workspace_id: uuid.UUID,
    state_id: uuid.UUID,
    reassign_to_id: uuid.UUID | None = Query(None),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKFLOW_STATE_MANAGE)),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> None:
    await service.delete(workspace_id, state_id, reassign_to_id)
