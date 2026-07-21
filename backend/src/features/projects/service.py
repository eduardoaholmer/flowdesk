import secrets
import uuid
from collections.abc import Mapping, Sequence

from src.core.project_key import derive_project_key, random_project_key
from src.core.security import CurrentUser
from src.core.slug import slugify
from src.features.projects.exceptions import (
    ProjectAlreadyArchivedError,
    ProjectHasActiveIssuesError,
    ProjectKeyTakenError,
    ProjectMemberNotInWorkspaceError,
    ProjectNameTakenError,
    ProjectNotArchivedError,
    ProjectNotFoundError,
    ProjectSlugTakenError,
)
from src.features.projects.models import Project, ProjectActivityLog, ProjectMember, ProjectStatus
from src.features.projects.repository import ProjectRepositoryProtocol, ProjectSort
from src.features.projects.schemas import ProjectCreateRequest, ProjectUpdateRequest, ProjectView
from src.features.workspaces.repository import WorkspaceRepositoryProtocol

_SLUG_COLLISION_RETRIES = 5
_KEY_COLLISION_RETRIES = 10


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepositoryProtocol,
        workspace_repo: WorkspaceRepositoryProtocol,
    ) -> None:
        """Sem `PermissionService` aqui, ao contrário de `WorkspaceService`: toda
        autorização de Projects é resolvida inteiramente por
        `Depends(require_permission(...))` no router (papel decide o caso geral,
        sem exceção de posse por recurso).

        `workspace_repo` entra só para validar que um usuário vinculado a um
        projeto (`ProjectMember`) já é membro do workspace — regra de negócio, não
        autorização (membership de projeto é informativa, ver `ProjectMember`).
        """
        self._project_repo = project_repo
        self._workspace_repo = workspace_repo

    async def create(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: ProjectCreateRequest
    ) -> ProjectView:
        if await self._project_repo.get_by_name(workspace_id, payload.name) is not None:
            raise ProjectNameTakenError()
        if payload.lead_id is not None and (
            await self._workspace_repo.get_member(workspace_id, payload.lead_id) is None
        ):
            raise ProjectMemberNotInWorkspaceError()
        slug = await self._resolve_slug(workspace_id, payload.name, payload.slug)
        key = await self._resolve_key(workspace_id, payload.name, payload.key)

        project = await self._project_repo.create(
            Project(
                workspace_id=workspace_id,
                name=payload.name,
                slug=slug,
                key=key,
                description=payload.description,
                icon=payload.icon,
                color=payload.color,
                target_date=payload.target_date,
                lead_id=payload.lead_id,
                created_by=current_user.id,
                status=ProjectStatus.ACTIVE,
            )
        )
        if project.lead_id is not None:
            await self._project_repo.add_member(
                ProjectMember(
                    workspace_id=workspace_id, project_id=project.id, user_id=project.lead_id
                )
            )
        await self._record_activity(
            workspace_id, project.id, current_user.id, "project.created", {"name": project.name}
        )
        return await self._build_view(project)

    async def list_for_workspace(
        self,
        workspace_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
        search: str | None,
        status: ProjectStatus | None,
        sort: ProjectSort,
    ) -> tuple[list[ProjectView], int]:
        projects = await self._project_repo.list_by_workspace(
            workspace_id, page=page, per_page=per_page, search=search, status=status, sort=sort
        )
        total = await self._project_repo.count_by_workspace(
            workspace_id, search=search, status=status
        )
        return await self._build_views(projects), total

    async def get(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> ProjectView:
        return await self._build_view(await self._get_active_project(workspace_id, project_id))

    async def update(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: ProjectUpdateRequest,
    ) -> ProjectView:
        project = await self._get_active_project(workspace_id, project_id)

        changes: dict[str, dict[str, object]] = {}
        if payload.name is not None and payload.name != project.name:
            existing = await self._project_repo.get_by_name(workspace_id, payload.name)
            if existing is not None and existing.id != project.id:
                raise ProjectNameTakenError()
            changes["name"] = {"old": project.name, "new": payload.name}
            project.name = payload.name
        if payload.slug is not None and payload.slug != project.slug:
            existing_by_slug = await self._project_repo.get_by_slug(workspace_id, payload.slug)
            if existing_by_slug is not None and existing_by_slug.id != project.id:
                raise ProjectSlugTakenError()
            changes["slug"] = {"old": project.slug, "new": payload.slug}
            project.slug = payload.slug
        if payload.key is not None and payload.key != project.key:
            existing_by_key = await self._project_repo.get_by_key(workspace_id, payload.key)
            if existing_by_key is not None and existing_by_key.id != project.id:
                raise ProjectKeyTakenError()
            changes["key"] = {"old": project.key, "new": payload.key}
            project.key = payload.key
        if payload.description is not None and payload.description != project.description:
            changes["description"] = {"old": project.description, "new": payload.description}
            project.description = payload.description
        if payload.icon is not None and payload.icon != project.icon:
            changes["icon"] = {"old": project.icon, "new": payload.icon}
            project.icon = payload.icon
        if payload.color is not None and payload.color != project.color:
            changes["color"] = {"old": project.color, "new": payload.color}
            project.color = payload.color
        if payload.target_date is not None and payload.target_date != project.target_date:
            changes["target_date"] = {
                "old": project.target_date.isoformat() if project.target_date else None,
                "new": payload.target_date.isoformat(),
            }
            project.target_date = payload.target_date
        if payload.lead_id is not None and payload.lead_id != project.lead_id:
            if await self._workspace_repo.get_member(workspace_id, payload.lead_id) is None:
                raise ProjectMemberNotInWorkspaceError()
            changes["lead_id"] = {
                "old": str(project.lead_id) if project.lead_id else None,
                "new": str(payload.lead_id),
            }
            project.lead_id = payload.lead_id
            await self._project_repo.add_member(
                ProjectMember(
                    workspace_id=workspace_id, project_id=project.id, user_id=payload.lead_id
                )
            )

        if changes:
            await self._project_repo.update(project)
            await self._record_activity(
                workspace_id, project.id, current_user.id, "project.updated", changes
            )
        return await self._build_view(project)

    async def archive(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, project_id: uuid.UUID
    ) -> ProjectView:
        project = await self._get_active_project(workspace_id, project_id)
        if project.status == ProjectStatus.ARCHIVED:
            raise ProjectAlreadyArchivedError()

        project.status = ProjectStatus.ARCHIVED
        await self._project_repo.update(project)
        await self._record_activity(
            workspace_id, project.id, current_user.id, "project.archived", {"name": project.name}
        )
        return await self._build_view(project)

    async def restore(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, project_id: uuid.UUID
    ) -> ProjectView:
        project = await self._get_active_project(workspace_id, project_id)
        if project.status == ProjectStatus.ACTIVE:
            raise ProjectNotArchivedError()

        project.status = ProjectStatus.ACTIVE
        await self._project_repo.update(project)
        await self._record_activity(
            workspace_id, project.id, current_user.id, "project.restored", {"name": project.name}
        )
        return await self._build_view(project)

    async def add_member(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectView:
        project = await self._get_active_project(workspace_id, project_id)
        if await self._workspace_repo.get_member(workspace_id, user_id) is None:
            raise ProjectMemberNotInWorkspaceError()

        added = await self._project_repo.add_member(
            ProjectMember(workspace_id=workspace_id, project_id=project_id, user_id=user_id)
        )
        if added:
            await self._record_activity(
                workspace_id,
                project_id,
                current_user.id,
                "project.member_added",
                {"user_id": str(user_id)},
            )
        return await self._build_view(project)

    async def remove_member(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectView:
        project = await self._get_active_project(workspace_id, project_id)
        removed = await self._project_repo.remove_member(project_id, user_id)
        if removed:
            await self._record_activity(
                workspace_id,
                project_id,
                current_user.id,
                "project.member_removed",
                {"user_id": str(user_id)},
            )
        return await self._build_view(project)

    async def delete(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, project_id: uuid.UUID
    ) -> None:
        project = await self._get_active_project(workspace_id, project_id)
        if await self._project_repo.has_active_issues(project.id):
            raise ProjectHasActiveIssuesError()

        await self._project_repo.soft_delete(project_id)
        await self._record_activity(
            workspace_id, project_id, current_user.id, "project.deleted", {"name": project.name}
        )

    async def _get_active_project(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        project = await self._project_repo.get_by_id(workspace_id, project_id)
        if project is None:
            raise ProjectNotFoundError()
        return project

    async def _build_view(self, project: Project) -> ProjectView:
        return (await self._build_views([project]))[0]

    async def _build_views(self, projects: Sequence[Project]) -> list[ProjectView]:
        ids = [p.id for p in projects]
        member_ids = await self._project_repo.list_member_ids(ids)
        counts = await self._project_repo.issue_counts(ids)
        return [
            ProjectView(
                project=p,
                member_ids=member_ids.get(p.id, []),
                issue_count=counts.get(p.id, (0, 0))[0],
                done_issue_count=counts.get(p.id, (0, 0))[1],
            )
            for p in projects
        ]

    async def _resolve_slug(
        self, workspace_id: uuid.UUID, name: str, requested_slug: str | None
    ) -> str:
        if requested_slug is not None:
            if await self._project_repo.get_by_slug(workspace_id, requested_slug) is not None:
                raise ProjectSlugTakenError()
            return requested_slug

        base = slugify(name)
        candidate = base
        for _ in range(_SLUG_COLLISION_RETRIES):
            if await self._project_repo.get_by_slug(workspace_id, candidate) is None:
                return candidate
            candidate = f"{base}-{secrets.token_hex(3)}"
        raise ProjectSlugTakenError()

    async def _resolve_key(
        self, workspace_id: uuid.UUID, name: str, requested_key: str | None
    ) -> str:
        if requested_key is not None:
            if await self._project_repo.get_by_key(workspace_id, requested_key) is not None:
                raise ProjectKeyTakenError()
            return requested_key

        candidate = derive_project_key(name)
        for _ in range(_KEY_COLLISION_RETRIES):
            if await self._project_repo.get_by_key(workspace_id, candidate) is None:
                return candidate
            candidate = random_project_key()
        raise ProjectKeyTakenError()

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        await self._project_repo.record_activity(
            ProjectActivityLog(
                workspace_id=workspace_id,
                project_id=project_id,
                actor_id=actor_id,
                action=action,
                metadata_=dict(metadata) if metadata is not None else None,
            )
        )
