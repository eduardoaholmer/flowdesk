import uuid

from fastapi import APIRouter, Depends, Query, status

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import CollectionEnvelope, DataEnvelope, PaginationMeta
from src.core.security import CurrentUser
from src.features.comments.dependencies import get_comment_service
from src.features.comments.schemas import (
    CommentCreateRequest,
    CommentResponse,
    CommentUpdateRequest,
)
from src.features.comments.service import CommentService
from src.features.workspaces.models import WorkspaceMember

# Um único router cobre dois formatos de path (`.../issues/{issue_id}/comments`
# para criar/listar, `.../comments/{comment_id}` para editar/excluir) — mesmo
# recurso, mesmo service, mesmo módulo (CLAUDE.md §4, "um router por recurso");
# a assimetria de path é a mesma já aceita por `invitations_router` (ADR-009,
# Decisão 6): o comentário-alvo de um PATCH/DELETE já se autoidentifica pelo
# próprio `comment_id`, sem precisar do `issue_id` no path.
router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["comments"])


@router.post(
    "/issues/{issue_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=DataEnvelope[CommentResponse],
)
async def create_comment(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    payload: CommentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.COMMENT_CREATE)),
    service: CommentService = Depends(get_comment_service),
) -> DataEnvelope[CommentResponse]:
    comment = await service.create(current_user, workspace_id, issue_id, payload)
    return DataEnvelope(data=CommentResponse.model_validate(comment))


@router.get(
    "/issues/{issue_id}/comments",
    response_model=CollectionEnvelope[CommentResponse],
)
async def list_comments(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: CommentService = Depends(get_comment_service),
) -> CollectionEnvelope[CommentResponse]:
    comments, total = await service.list_for_issue(
        workspace_id, issue_id, page=page, per_page=per_page
    )
    return CollectionEnvelope(
        data=[CommentResponse.model_validate(c) for c in comments],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.patch("/comments/{comment_id}", response_model=DataEnvelope[CommentResponse])
async def update_comment(
    workspace_id: uuid.UUID,
    comment_id: uuid.UUID,
    payload: CommentUpdateRequest,
    acting_member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: CommentService = Depends(get_comment_service),
) -> DataEnvelope[CommentResponse]:
    comment = await service.update(acting_member, workspace_id, comment_id, payload)
    return DataEnvelope(data=CommentResponse.model_validate(comment))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    workspace_id: uuid.UUID,
    comment_id: uuid.UUID,
    acting_member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: CommentService = Depends(get_comment_service),
) -> None:
    await service.delete(acting_member, workspace_id, comment_id)
