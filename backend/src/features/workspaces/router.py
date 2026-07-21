import uuid

from fastapi import APIRouter, Depends, Query, status

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import CollectionEnvelope, DataEnvelope, PaginationMeta
from src.core.security import CurrentUser
from src.features.workspaces.dependencies import get_invitation_service, get_workspace_service
from src.features.workspaces.models import WorkspaceMember, WorkspaceRole
from src.features.workspaces.schemas import (
    InvitationCreatedResponse,
    InvitationCreateRequest,
    InvitationResponse,
    MemberUpdateRoleRequest,
    WorkspaceCreateRequest,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from src.features.workspaces.service import InvitationService, WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
invitations_router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[WorkspaceResponse]
)
async def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> DataEnvelope[WorkspaceResponse]:
    workspace = await service.create(current_user, payload)
    return DataEnvelope(data=WorkspaceResponse.model_validate(workspace))


@router.get("", response_model=CollectionEnvelope[WorkspaceResponse])
async def list_workspaces(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> CollectionEnvelope[WorkspaceResponse]:
    workspaces, total = await service.list_for_user(current_user, page=page, per_page=per_page)
    return CollectionEnvelope(
        data=[WorkspaceResponse.model_validate(w) for w in workspaces],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.get("/{workspace_id}", response_model=DataEnvelope[WorkspaceResponse])
async def get_workspace(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_VIEW)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> DataEnvelope[WorkspaceResponse]:
    workspace = await service.get(workspace_id)
    return DataEnvelope(data=WorkspaceResponse.model_validate(workspace))


@router.patch("/{workspace_id}", response_model=DataEnvelope[WorkspaceResponse])
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_UPDATE)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> DataEnvelope[WorkspaceResponse]:
    workspace = await service.update(current_user, workspace_id, payload)
    return DataEnvelope(data=WorkspaceResponse.model_validate(workspace))


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_DELETE)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    await service.delete(current_user, workspace_id)


@router.get("/{workspace_id}/members", response_model=CollectionEnvelope[WorkspaceMemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: WorkspaceRole | None = Query(None),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_VIEW)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> CollectionEnvelope[WorkspaceMemberResponse]:
    members, total = await service.list_members(
        workspace_id, page=page, per_page=per_page, role=role
    )
    return CollectionEnvelope(
        data=[WorkspaceMemberResponse.from_member(m) for m in members],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.delete("/{workspace_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    """Não passa por `require_permission`: sair não é uma permissão condicionada
    a papel, é o direito de qualquer membro sobre a própria associação — a
    checagem de posse acontece dentro de `WorkspaceService.leave`.
    """
    await service.leave(current_user, workspace_id)


@router.patch(
    "/{workspace_id}/members/{member_id}", response_model=DataEnvelope[WorkspaceMemberResponse]
)
async def update_member_role(
    workspace_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: MemberUpdateRoleRequest,
    current_user: CurrentUser = Depends(get_current_user),
    acting_member: WorkspaceMember = Depends(require_permission(Permission.MEMBER_UPDATE_ROLE)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> DataEnvelope[WorkspaceMemberResponse]:
    member = await service.update_member_role(
        current_user, workspace_id, member_id, payload.role, acting_member.role
    )
    return DataEnvelope(data=WorkspaceMemberResponse.from_member(member))


@router.post(
    "/{workspace_id}/members/{member_id}/transfer-ownership",
    response_model=DataEnvelope[WorkspaceResponse],
)
async def transfer_ownership(
    workspace_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_TRANSFER_OWNERSHIP)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> DataEnvelope[WorkspaceResponse]:
    workspace = await service.transfer_ownership(current_user, workspace_id, member_id)
    return DataEnvelope(data=WorkspaceResponse.model_validate(workspace))


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    acting_member: WorkspaceMember = Depends(require_permission(Permission.MEMBER_REMOVE)),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    await service.remove_member(current_user, workspace_id, member_id, acting_member.role)


@router.post(
    "/{workspace_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=DataEnvelope[InvitationCreatedResponse],
)
async def create_invitation(
    workspace_id: uuid.UUID,
    payload: InvitationCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_INVITE)),
    service: InvitationService = Depends(get_invitation_service),
) -> DataEnvelope[InvitationCreatedResponse]:
    issued = await service.create(current_user, workspace_id, payload)
    response = InvitationCreatedResponse.from_issued(issued.invitation, issued.token)
    return DataEnvelope(data=response)


@router.get("/{workspace_id}/invitations", response_model=CollectionEnvelope[InvitationResponse])
async def list_invitations(
    workspace_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_INVITE)),
    service: InvitationService = Depends(get_invitation_service),
) -> CollectionEnvelope[InvitationResponse]:
    invitations, total = await service.list_for_workspace(
        workspace_id, page=page, per_page=per_page
    )
    return CollectionEnvelope(
        data=[InvitationResponse.from_invitation(i) for i in invitations],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.delete(
    "/{workspace_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_invitation(
    workspace_id: uuid.UUID,
    invitation_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_INVITE)),
    service: InvitationService = Depends(get_invitation_service),
) -> None:
    await service.cancel(workspace_id, invitation_id)


@invitations_router.post("/{token}/accept", response_model=DataEnvelope[WorkspaceMemberResponse])
async def accept_invitation(
    token: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> DataEnvelope[WorkspaceMemberResponse]:
    member = await service.accept(current_user, token)
    return DataEnvelope(data=WorkspaceMemberResponse.from_member(member))
