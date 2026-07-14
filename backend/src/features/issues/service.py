import uuid
from collections.abc import Sequence

from src.core.authorization import PermissionService
from src.core.permissions import Permission
from src.core.security import CurrentUser
from src.features.issues.exceptions import (
    IssueLabelAlreadyAppliedError,
    IssueNotFoundError,
    IssueVersionConflictError,
)
from src.features.issues.models import ActivityLog, Issue, IssuePriority, IssueStatus
from src.features.issues.repository import IssueRepositoryProtocol, IssueSort
from src.features.issues.schemas import IssueCreateRequest, IssueUpdateRequest
from src.features.labels.exceptions import LabelNotFoundError
from src.features.labels.models import Label
from src.features.labels.repository import LabelRepositoryProtocol
from src.features.projects.exceptions import ProjectNotFoundError
from src.features.projects.repository import ProjectRepositoryProtocol
from src.features.workspaces.models import WorkspaceMember


class IssueService:
    def __init__(
        self,
        issue_repo: IssueRepositoryProtocol,
        permission_service: PermissionService,
        project_repo: ProjectRepositoryProtocol,
        label_repo: LabelRepositoryProtocol,
    ) -> None:
        """Recebe `PermissionService`, ao contrário de `ProjectService`: excluir
        uma issue tem posse-como-exceção (`Permission.ISSUE_DELETE` está em
        `OWNERSHIP_OVERRIDE_PERMISSIONS`) — uma checagem contextual que só é
        resolvível depois que a issue já foi buscada (`docs/09-decision-log.md`
        ADR-012, Decisão 6), mesmo padrão de `WorkspaceService`.

        `project_repo` valida que `project_id` (quando informado) pertence ao
        mesmo workspace da issue — CLAUDE.md §18 exige essa checagem explícita,
        não apenas confiar na FK (soft delete não aciona `ON DELETE RESTRICT`).

        `label_repo` (Sprint 8) é usado só pela associação Label<->Issue
        (`add_label`/`remove_label`/`list_labels`) — `IssueRepository` já é o
        "guarda-chuva" de `IssueLabel` (a tabela de associação em si vive em
        `features/issues/models.py`), mas validar que o `label_id` recebido
        existe e pertence ao mesmo workspace é responsabilidade do agregado
        Label, não de Issue.
        """
        self._issue_repo = issue_repo
        self._permission_service = permission_service
        self._project_repo = project_repo
        self._label_repo = label_repo

    async def create(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: IssueCreateRequest
    ) -> Issue:
        if payload.project_id is not None:
            await self._get_active_project(workspace_id, payload.project_id)

        number = await self._issue_repo.next_number(workspace_id)
        issue = await self._issue_repo.create(
            Issue(
                workspace_id=workspace_id,
                project_id=payload.project_id,
                number=number,
                title=payload.title,
                description=payload.description,
                status=payload.status,
                priority=payload.priority,
                assignee_id=payload.assignee_id,
                creator_id=current_user.id,
                estimate=payload.estimate,
                due_date=payload.due_date,
            )
        )
        await self._record_activity(
            workspace_id,
            issue.id,
            current_user.id,
            "issue.created",
            new_value=issue.identifier,
        )
        return issue

    async def list_for_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
        project_id: uuid.UUID | None,
        status: IssueStatus | None,
        priority: IssuePriority | None,
        assignee_id: uuid.UUID | None,
        creator_id: uuid.UUID | None,
        search: str | None,
        sort: IssueSort,
    ) -> tuple[Sequence[Issue], int]:
        issues = await self._issue_repo.list_by_workspace(
            workspace_id,
            page=page,
            per_page=per_page,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            creator_id=creator_id,
            search=search,
            sort=sort,
        )
        total = await self._issue_repo.count_by_workspace(
            workspace_id,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            creator_id=creator_id,
            search=search,
        )
        return issues, total

    async def get(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue:
        return await self._get_active_issue(workspace_id, issue_id)

    async def list_activity(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> Sequence[ActivityLog]:
        await self._get_active_issue(workspace_id, issue_id)
        return await self._issue_repo.list_activity(issue_id)

    async def list_labels(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Sequence[Label]:
        await self._get_active_issue(workspace_id, issue_id)
        return await self._issue_repo.list_labels(issue_id)

    async def add_label(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        label_id: uuid.UUID,
    ) -> Label:
        issue = await self._get_active_issue(workspace_id, issue_id)
        label = await self._label_repo.get_by_id(workspace_id, label_id)
        if label is None:
            raise LabelNotFoundError()
        if await self._issue_repo.get_label_link(issue.id, label_id) is not None:
            raise IssueLabelAlreadyAppliedError()

        await self._issue_repo.add_label(issue.id, label_id)
        await self._record_activity(
            workspace_id,
            issue.id,
            current_user.id,
            "label.added",
            new_value=label.name,
        )
        return label

    async def remove_label(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        label_id: uuid.UUID,
    ) -> None:
        issue = await self._get_active_issue(workspace_id, issue_id)
        label = await self._label_repo.get_by_id(workspace_id, label_id)
        if label is None:
            raise LabelNotFoundError()

        await self._issue_repo.remove_label(issue.id, label_id)
        await self._record_activity(
            workspace_id,
            issue.id,
            current_user.id,
            "label.removed",
            old_value=label.name,
        )

    async def update(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        payload: IssueUpdateRequest,
        expected_version: int | None = None,
    ) -> Issue:
        issue = await self._get_active_issue(workspace_id, issue_id)
        if expected_version is not None and expected_version != issue.version:
            raise IssueVersionConflictError()

        changed = False

        if payload.title is not None and payload.title != issue.title:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.updated",
                field="title",
                old_value=issue.title,
                new_value=payload.title,
            )
            issue.title = payload.title
            changed = True

        if payload.description is not None and payload.description != issue.description:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.updated",
                field="description",
                old_value=issue.description,
                new_value=payload.description,
            )
            issue.description = payload.description
            changed = True

        if payload.project_id is not None and payload.project_id != issue.project_id:
            await self._get_active_project(workspace_id, payload.project_id)
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.updated",
                field="project_id",
                old_value=str(issue.project_id) if issue.project_id else None,
                new_value=str(payload.project_id),
            )
            issue.project_id = payload.project_id
            changed = True

        if payload.status is not None and payload.status != issue.status:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.status_changed",
                field="status",
                old_value=issue.status.value,
                new_value=payload.status.value,
            )
            issue.status = payload.status
            changed = True

        if payload.priority is not None and payload.priority != issue.priority:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.priority_changed",
                field="priority",
                old_value=issue.priority.value,
                new_value=payload.priority.value,
            )
            issue.priority = payload.priority
            changed = True

        if payload.assignee_id is not None and payload.assignee_id != issue.assignee_id:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.assignee_changed",
                field="assignee_id",
                old_value=str(issue.assignee_id) if issue.assignee_id else None,
                new_value=str(payload.assignee_id),
            )
            issue.assignee_id = payload.assignee_id
            changed = True

        if payload.estimate is not None and payload.estimate != issue.estimate:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.updated",
                field="estimate",
                old_value=str(issue.estimate) if issue.estimate is not None else None,
                new_value=str(payload.estimate),
            )
            issue.estimate = payload.estimate
            changed = True

        if payload.due_date is not None and payload.due_date != issue.due_date:
            await self._record_activity(
                workspace_id,
                issue.id,
                current_user.id,
                "issue.updated",
                field="due_date",
                old_value=issue.due_date.isoformat() if issue.due_date else None,
                new_value=payload.due_date.isoformat(),
            )
            issue.due_date = payload.due_date
            changed = True

        if changed:
            issue.version += 1
            await self._issue_repo.update(issue)
        return issue

    async def delete(
        self, acting_member: WorkspaceMember, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> None:
        issue = await self._get_active_issue(workspace_id, issue_id)
        self._permission_service.require(
            member=acting_member,
            permission=Permission.ISSUE_DELETE,
            resource_owner_id=issue.creator_id,
        )
        await self._issue_repo.soft_delete(issue_id)
        await self._record_activity(
            workspace_id,
            issue_id,
            acting_member.user_id,
            "issue.deleted",
            old_value=issue.identifier,
        )

    async def _get_active_issue(self, workspace_id: uuid.UUID, issue_id: uuid.UUID) -> Issue:
        issue = await self._issue_repo.get_by_id(workspace_id, issue_id)
        if issue is None:
            raise IssueNotFoundError()
        return issue

    async def _get_active_project(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> None:
        project = await self._project_repo.get_by_id(workspace_id, project_id)
        if project is None:
            raise ProjectNotFoundError()

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        issue_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        *,
        field: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> None:
        await self._issue_repo.record_activity(
            ActivityLog(
                workspace_id=workspace_id,
                issue_id=issue_id,
                actor_id=actor_id,
                action=action,
                field=field,
                old_value=old_value,
                new_value=new_value,
            )
        )
