import uuid
from collections.abc import Mapping, Sequence

from src.core.security import CurrentUser
from src.features.labels.exceptions import LabelNameTakenError, LabelNotFoundError
from src.features.labels.models import Label, LabelActivityLog
from src.features.labels.repository import LabelRepositoryProtocol
from src.features.labels.schemas import LabelCreateRequest, LabelUpdateRequest


class LabelService:
    def __init__(self, label_repo: LabelRepositoryProtocol) -> None:
        """Sem `PermissionService`, mesmo racional de `ProjectService`: toda
        autorização de Labels é resolvida inteiramente por
        `Depends(require_permission(...))` no router — não há regra de posse
        por recurso (ao contrário de `comment.update`/`issue.delete`).
        """
        self._label_repo = label_repo

    async def create(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, payload: LabelCreateRequest
    ) -> Label:
        if await self._label_repo.get_by_name(workspace_id, payload.name) is not None:
            raise LabelNameTakenError()

        label = await self._label_repo.create(
            Label(
                workspace_id=workspace_id,
                name=payload.name,
                color=payload.color,
                description=payload.description,
            )
        )
        await self._record_activity(
            workspace_id, label.id, current_user.id, "label.created", {"name": label.name}
        )
        return label

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[Label]:
        return await self._label_repo.list_by_workspace(workspace_id)

    async def get(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label:
        return await self._get_active_label(workspace_id, label_id)

    async def update(
        self,
        current_user: CurrentUser,
        workspace_id: uuid.UUID,
        label_id: uuid.UUID,
        payload: LabelUpdateRequest,
    ) -> Label:
        label = await self._get_active_label(workspace_id, label_id)

        changes: dict[str, dict[str, object]] = {}
        if payload.name is not None and payload.name != label.name:
            existing = await self._label_repo.get_by_name(workspace_id, payload.name)
            if existing is not None and existing.id != label.id:
                raise LabelNameTakenError()
            changes["name"] = {"old": label.name, "new": payload.name}
            label.name = payload.name
        if payload.color is not None and payload.color != label.color:
            changes["color"] = {"old": label.color, "new": payload.color}
            label.color = payload.color
        if payload.description is not None and payload.description != label.description:
            changes["description"] = {"old": label.description, "new": payload.description}
            label.description = payload.description

        if changes:
            await self._label_repo.update(label)
            await self._record_activity(
                workspace_id, label.id, current_user.id, "label.updated", changes
            )
        return label

    async def delete(
        self, current_user: CurrentUser, workspace_id: uuid.UUID, label_id: uuid.UUID
    ) -> None:
        label = await self._get_active_label(workspace_id, label_id)
        await self._label_repo.soft_delete(label_id)
        await self._record_activity(
            workspace_id, label_id, current_user.id, "label.deleted", {"name": label.name}
        )

    async def _get_active_label(self, workspace_id: uuid.UUID, label_id: uuid.UUID) -> Label:
        label = await self._label_repo.get_by_id(workspace_id, label_id)
        if label is None:
            raise LabelNotFoundError()
        return label

    async def _record_activity(
        self,
        workspace_id: uuid.UUID,
        label_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        await self._label_repo.record_activity(
            LabelActivityLog(
                workspace_id=workspace_id,
                label_id=label_id,
                actor_id=actor_id,
                action=action,
                metadata_=dict(metadata) if metadata is not None else None,
            )
        )
