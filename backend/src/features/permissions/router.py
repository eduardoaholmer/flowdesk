import uuid

from fastapi import APIRouter, Depends

from src.core.authorization import require_permission
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.features.permissions.dependencies import get_permission_override_service
from src.features.permissions.schemas import (
    PermissionMatrixEntryResponse,
    PermissionOverrideUpsertRequest,
)
from src.features.permissions.service import PermissionOverrideService
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/permission-overrides", tags=["permissions"])


@router.get("", response_model=DataEnvelope[list[PermissionMatrixEntryResponse]])
async def list_permission_matrix(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_MANAGE_PERMISSIONS)),
    service: PermissionOverrideService = Depends(get_permission_override_service),
) -> DataEnvelope[list[PermissionMatrixEntryResponse]]:
    entries = await service.list_matrix(workspace_id)
    return DataEnvelope(data=entries)


@router.put("", response_model=DataEnvelope[list[PermissionMatrixEntryResponse]])
async def set_permission_override(
    workspace_id: uuid.UUID,
    payload: PermissionOverrideUpsertRequest,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_MANAGE_PERMISSIONS)),
    service: PermissionOverrideService = Depends(get_permission_override_service),
) -> DataEnvelope[list[PermissionMatrixEntryResponse]]:
    entries = await service.set_override(
        workspace_id, payload.role, payload.permission, payload.granted
    )
    return DataEnvelope(data=entries)
