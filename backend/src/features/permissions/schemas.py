from pydantic import BaseModel

from src.core.permissions import Permission
from src.features.workspaces.models import WorkspaceRole


class PermissionOverrideUpsertRequest(BaseModel):
    role: WorkspaceRole
    permission: Permission
    granted: bool


class PermissionMatrixEntryResponse(BaseModel):
    """Uma célula da matriz permissão × papel exibida na UI de gerenciamento.

    `default` é o valor de `ROLE_PERMISSIONS` (`core/authorization.py`) sem
    nenhum override; `effective` já aplica o `PermissionOverride` do workspace,
    se houver um para este par; `is_override` diz à UI se o valor exibido
    diverge do padrão (para destacar visualmente a customização)."""

    permission: Permission
    role: WorkspaceRole
    default: bool
    effective: bool
    is_override: bool
