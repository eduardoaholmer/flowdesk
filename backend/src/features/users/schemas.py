import uuid

from pydantic import BaseModel

from src.features.auth.schemas import UserResponse
from src.features.workspaces.models import WorkspaceRole


class WorkspaceMembershipSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: WorkspaceRole


class UserProfileResponse(UserResponse):
    """`GET /users/me` reintroduz `workspaces` (ADR-008, impacto futuro) agora
    que `WorkspaceMember` tem uma API própria — a Sprint 3 devolvia só `UserResponse`
    porque Workspaces ainda não existia.
    """

    workspaces: list[WorkspaceMembershipSummary]
