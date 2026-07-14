import uuid

from fastapi import APIRouter, Depends, Header, Query, status

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import CollectionEnvelope, DataEnvelope, PaginationMeta
from src.core.security import CurrentUser
from src.features.issues.dependencies import get_issue_service
from src.features.issues.models import IssuePriority, IssueStatus
from src.features.issues.repository import IssueSort
from src.features.issues.schemas import (
    IssueActivityLogResponse,
    IssueCreateRequest,
    IssueLabelAddRequest,
    IssueResponse,
    IssueUpdateRequest,
)
from src.features.issues.service import IssueService
from src.features.labels.schemas import LabelResponse
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/issues", tags=["issues"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[IssueResponse])
async def create_issue(
    workspace_id: uuid.UUID,
    payload: IssueCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_CREATE)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[IssueResponse]:
    issue = await service.create(current_user, workspace_id, payload)
    return DataEnvelope(data=IssueResponse.model_validate(issue))


@router.get("", response_model=CollectionEnvelope[IssueResponse])
async def list_issues(
    workspace_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    project_id: uuid.UUID | None = Query(None),
    status_filter: IssueStatus | None = Query(None, alias="status"),
    priority: IssuePriority | None = Query(None),
    assignee_id: uuid.UUID | None = Query(None),
    creator_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None, min_length=1, max_length=200),
    sort: IssueSort = Query("-updated_at"),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: IssueService = Depends(get_issue_service),
) -> CollectionEnvelope[IssueResponse]:
    issues, total = await service.list_for_workspace(
        workspace_id,
        page=page,
        per_page=per_page,
        project_id=project_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        creator_id=creator_id,
        search=q,
        sort=sort,
    )
    return CollectionEnvelope(
        data=[IssueResponse.model_validate(i) for i in issues],
        meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
    )


@router.get("/{issue_id}", response_model=DataEnvelope[IssueResponse])
async def get_issue(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[IssueResponse]:
    issue = await service.get(workspace_id, issue_id)
    return DataEnvelope(data=IssueResponse.model_validate(issue))


@router.get("/{issue_id}/activity", response_model=DataEnvelope[list[IssueActivityLogResponse]])
async def list_issue_activity(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[list[IssueActivityLogResponse]]:
    entries = await service.list_activity(workspace_id, issue_id)
    return DataEnvelope(data=[IssueActivityLogResponse.model_validate(e) for e in entries])


@router.patch("/{issue_id}", response_model=DataEnvelope[IssueResponse])
async def update_issue(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    payload: IssueUpdateRequest,
    if_match: int | None = Header(default=None, alias="If-Match"),
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_UPDATE)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[IssueResponse]:
    issue = await service.update(
        current_user, workspace_id, issue_id, payload, expected_version=if_match
    )
    return DataEnvelope(data=IssueResponse.model_validate(issue))


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    acting_member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: IssueService = Depends(get_issue_service),
) -> None:
    await service.delete(acting_member, workspace_id, issue_id)


@router.get("/{issue_id}/labels", response_model=DataEnvelope[list[LabelResponse]])
async def list_issue_labels(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[list[LabelResponse]]:
    labels = await service.list_labels(workspace_id, issue_id)
    return DataEnvelope(data=[LabelResponse.model_validate(label) for label in labels])


@router.post(
    "/{issue_id}/labels",
    status_code=status.HTTP_201_CREATED,
    response_model=DataEnvelope[LabelResponse],
)
async def add_issue_label(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    payload: IssueLabelAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_UPDATE)),
    service: IssueService = Depends(get_issue_service),
) -> DataEnvelope[LabelResponse]:
    label = await service.add_label(current_user, workspace_id, issue_id, payload.label_id)
    return DataEnvelope(data=LabelResponse.model_validate(label))


@router.delete("/{issue_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_issue_label(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_UPDATE)),
    service: IssueService = Depends(get_issue_service),
) -> None:
    await service.remove_label(current_user, workspace_id, issue_id, label_id)
