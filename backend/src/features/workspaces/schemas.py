import enum
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.core.slug import validate_slug_format as _validate_slug_format
from src.features.auth.schemas import UserResponse
from src.features.workspaces.models import Invitation, WorkspaceMember, WorkspaceRole


class WorkspaceCreateRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("O nome do workspace deve ter ao menos 2 caracteres.")
        return stripped

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        return _validate_slug_format(value) if value is not None else None


class WorkspaceUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("O nome do workspace deve ter ao menos 2 caracteres.")
        return stripped

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        return _validate_slug_format(value) if value is not None else None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    role: WorkspaceRole
    status: str
    joined_at: datetime
    user: UserResponse

    @classmethod
    def from_member(cls, member: WorkspaceMember) -> "WorkspaceMemberResponse":
        """`status` não é uma coluna própria: uma `WorkspaceMember` só existe
        (não soft-deletada) enquanto ativa — convite pendente é `Invitation`,
        uma entidade separada, nunca uma membership em estado intermediário.
        Exposto como campo fixo (`"ACTIVE"`) porque o contrato desta sprint pede
        `status` visível no membro; não impede introduzir outros estados depois.
        """
        return cls(
            id=member.id,
            workspace_id=member.workspace_id,
            role=member.role,
            status="ACTIVE",
            joined_at=member.created_at,
            user=UserResponse.model_validate(member.user),
        )


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: WorkspaceRole

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            raise ValueError("Não é possível convidar diretamente como OWNER.")
        return value


class MemberUpdateRoleRequest(BaseModel):
    role: WorkspaceRole

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            raise ValueError("Não é possível promover um membro a OWNER por este endpoint.")
        return value


class InvitationStatus(enum.StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"


class InvitationResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    email: str
    role: WorkspaceRole
    status: InvitationStatus
    invited_by_id: uuid.UUID
    expires_at: datetime
    created_at: datetime

    @classmethod
    def from_invitation(cls, invitation: Invitation) -> "InvitationResponse":
        return cls(
            id=invitation.id,
            workspace_id=invitation.workspace_id,
            email=invitation.email,
            role=invitation.role,
            status=_compute_status(invitation),
            invited_by_id=invitation.invited_by_id,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )


class InvitationCreatedResponse(InvitationResponse):
    """Só a resposta de criação carrega `token` em texto plano — o banco guarda
    apenas o hash (`token_hash`), então esta é a única oportunidade de expor o
    valor; nenhuma listagem subsequente o repete. Substitui o envio por e-mail
    transacional, fora do escopo de infraestrutura desta sprint (ver ADR-009).
    """

    token: str

    @classmethod
    def from_issued(cls, invitation: Invitation, token: str) -> "InvitationCreatedResponse":
        base = InvitationResponse.from_invitation(invitation)
        return cls(**base.model_dump(), token=token)


def _compute_status(invitation: Invitation) -> InvitationStatus:
    if invitation.accepted_at is not None:
        return InvitationStatus.ACCEPTED
    if invitation.expires_at < datetime.now(UTC):
        return InvitationStatus.EXPIRED
    return InvitationStatus.PENDING
