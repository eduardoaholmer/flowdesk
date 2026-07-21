import uuid

from fastapi import APIRouter, Depends, Query, status

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import CollectionEnvelope, DataEnvelope, PaginationMeta
from src.core.security import CurrentUser
from src.features.projects.dependencies import get_project_service
from src.features.projects.models import ProjectStatus
from src.features.projects.repository import ProjectSort
from src.features.projects.schemas import (
    ProjectCreateRequest,
    ProjectMemberAddRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from src.features.projects.service import ProjectService
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[ProjectResponse])
async def create_project(
    workspace_id: uuid.UUID,
    payload: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_CREATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.create(current_user, workspace_id, payload)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.get("", response_model=CollectionEnvelope[ProjectResponse])
async def list_projects(
    workspace_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    sort: ProjectSort = Query("-created_at"),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_READ)),
    service: ProjectService = Depends(get_project_service),
) -> CollectionEnvelope[ProjectResponse]:
    views, total = await service.list_for_workspace(
        workspace_id, page=page, per_page=per_page, search=search, status=status_filter, sort=sort
    )
    return CollectionEnvelope(
        data=[ProjectResponse.from_view(view) for view in views],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.get("/{project_id}", response_model=DataEnvelope[ProjectResponse])
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_READ)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.get(workspace_id, project_id)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.patch("/{project_id}", response_model=DataEnvelope[ProjectResponse])
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.update(current_user, workspace_id, project_id, payload)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.post("/{project_id}/archive", response_model=DataEnvelope[ProjectResponse])
async def archive_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.archive(current_user, workspace_id, project_id)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.post("/{project_id}/restore", response_model=DataEnvelope[ProjectResponse])
async def restore_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.restore(current_user, workspace_id, project_id)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.post(
    "/{project_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=DataEnvelope[ProjectResponse],
)
async def add_project_member(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectMemberAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.add_member(current_user, workspace_id, project_id, payload.user_id)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.delete("/{project_id}/members/{user_id}", response_model=DataEnvelope[ProjectResponse])
async def remove_project_member(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
    service: ProjectService = Depends(get_project_service),
) -> DataEnvelope[ProjectResponse]:
    view = await service.remove_member(current_user, workspace_id, project_id, user_id)
    return DataEnvelope(data=ProjectResponse.from_view(view))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.PROJECT_DELETE)),
    service: ProjectService = Depends(get_project_service),
) -> None:
    await service.delete(current_user, workspace_id, project_id)
