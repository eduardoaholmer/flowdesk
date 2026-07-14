import uuid

from fastapi import APIRouter, Depends, status

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.core.security import CurrentUser
from src.features.labels.dependencies import get_label_service
from src.features.labels.schemas import LabelCreateRequest, LabelResponse, LabelUpdateRequest
from src.features.labels.service import LabelService
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/labels", tags=["labels"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[LabelResponse])
async def create_label(
    workspace_id: uuid.UUID,
    payload: LabelCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.LABEL_CREATE)),
    service: LabelService = Depends(get_label_service),
) -> DataEnvelope[LabelResponse]:
    label = await service.create(current_user, workspace_id, payload)
    return DataEnvelope(data=LabelResponse.model_validate(label))


@router.get("", response_model=DataEnvelope[list[LabelResponse]])
async def list_labels(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.LABEL_READ)),
    service: LabelService = Depends(get_label_service),
) -> DataEnvelope[list[LabelResponse]]:
    labels = await service.list_for_workspace(workspace_id)
    return DataEnvelope(data=[LabelResponse.model_validate(label) for label in labels])


@router.get("/{label_id}", response_model=DataEnvelope[LabelResponse])
async def get_label(
    workspace_id: uuid.UUID,
    label_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.LABEL_READ)),
    service: LabelService = Depends(get_label_service),
) -> DataEnvelope[LabelResponse]:
    label = await service.get(workspace_id, label_id)
    return DataEnvelope(data=LabelResponse.model_validate(label))


@router.patch("/{label_id}", response_model=DataEnvelope[LabelResponse])
async def update_label(
    workspace_id: uuid.UUID,
    label_id: uuid.UUID,
    payload: LabelUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.LABEL_UPDATE)),
    service: LabelService = Depends(get_label_service),
) -> DataEnvelope[LabelResponse]:
    label = await service.update(current_user, workspace_id, label_id, payload)
    return DataEnvelope(data=LabelResponse.model_validate(label))


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    workspace_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.LABEL_DELETE)),
    service: LabelService = Depends(get_label_service),
) -> None:
    await service.delete(current_user, workspace_id, label_id)
