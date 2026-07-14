from fastapi import APIRouter, Depends

from src.core.dependencies import get_current_user
from src.core.schemas import DataEnvelope
from src.core.security import CurrentUser
from src.features.auth.schemas import UserResponse
from src.features.users.dependencies import get_user_service
from src.features.users.schemas import UserProfileResponse, WorkspaceMembershipSummary
from src.features.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=DataEnvelope[UserProfileResponse])
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> DataEnvelope[UserProfileResponse]:
    profile = await service.get_profile(current_user.id)
    workspaces = [
        WorkspaceMembershipSummary(
            id=membership.workspace.id,
            name=membership.workspace.name,
            slug=membership.workspace.slug,
            role=membership.role,
        )
        for membership in profile.memberships
    ]
    response = UserProfileResponse(
        **UserResponse.model_validate(profile.user).model_dump(), workspaces=workspaces
    )
    return DataEnvelope(data=response)
