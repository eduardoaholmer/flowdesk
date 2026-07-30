"""Sistema central de autorização (RBAC) do FlowDesk — Sprint 5.

Fluxo obrigatório (`CLAUDE.md` §10, `docs/02-architecture.md`):

    Request -> Authentication -> Workspace Context -> Permission Service
            -> Service Layer -> Repository

Nenhuma outra camada reimplementa checagem de papel/permissão: routers
declaram `Depends(require_permission(...))`; services que precisam de uma
checagem contextual adicional (dependente de um recurso já buscado, ex.:
"ADMIN não pode alterar um OWNER") chamam `PermissionService` diretamente —
nunca um `if member.role == ...` solto.

Exceção deliberada de camadas: este módulo vive em `core/` (transversal) mas
importa `features.workspaces.{models,repository,exceptions}` — uma decisão de
que toda checagem de permissão depende de resolver a associação do chamador
com o workspace (`WorkspaceMember`), o "tenant boundary" do sistema. Duplicar
essa resolução em cada feature futura (issues, comments, projects) seria
exatamente o tipo de reimplementação que esta sprint elimina. Ver ADR-010 em
`docs/09-decision-log.md`. Para evitar import circular com
`features/workspaces/dependencies.py` (que importa deste módulo para montar
`WorkspaceService`), este arquivo constrói `WorkspaceRepository` diretamente a
partir da sessão em vez de depender da factory `get_workspace_repository` —
mesmo padrão aplicado a `features/permissions/repository.py` (Sprint 9.3,
ADR-058) para resolver os overrides de permissão do chamador.
"""

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.core.dependencies import get_current_user
from src.core.exceptions import PermissionDeniedError
from src.core.logging import get_logger
from src.core.permissions import Permission
from src.core.security import CurrentUser
from src.features.permissions.repository import PermissionOverrideRepository
from src.features.workspaces.exceptions import CannotManageOwnerError, WorkspaceNotFoundError
from src.features.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from src.features.workspaces.repository import WorkspaceRepository, WorkspaceRepositoryProtocol

logger = get_logger(__name__)

# Permissões exclusivas do OWNER, nunca alcançáveis por override (Sprint 9.3,
# ADR-058) — as duas ações irreversíveis/de posse do domínio (excluir/transferir
# o workspace) mais a própria capacidade de gerenciar overrides (evita um ADMIN
# se auto-conceder qualquer uma das duas primeiras via toggle).
LOCKED_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_TRANSFER_OWNERSHIP,
        Permission.WORKSPACE_MANAGE_PERMISSIONS,
    }
)

# Matriz de permissões por papel — a fonte de verdade é esta constante, a
# documentação em `docs/07-security.md` §8 é a sua descrição legível para
# humanos (divergência entre as duas é bug, nunca o contrário). É o *default*
# por papel; um workspace pode desviar disso por permissão via
# `PermissionOverride` (Sprint 9.3) — ver `PermissionService.can` abaixo.
#
# OWNER tem toda permissão que existe hoje ou vier a existir (`frozenset(Permission)`
# reavalia o enum inteiro, então uma permissão nova automaticamente cai aqui sem
# exigir edição desta linha). ADMIN tem tudo exceto `LOCKED_PERMISSIONS`.
ROLE_PERMISSIONS: dict[WorkspaceRole, frozenset[Permission]] = {
    WorkspaceRole.OWNER: frozenset(Permission),
    WorkspaceRole.ADMIN: frozenset(Permission) - LOCKED_PERMISSIONS,
    WorkspaceRole.MEMBER: frozenset(
        {
            Permission.WORKSPACE_VIEW,
            Permission.PROJECT_READ,
            Permission.ISSUE_CREATE,
            Permission.ISSUE_READ,
            Permission.ISSUE_UPDATE,
            Permission.ISSUE_ASSIGN,
            Permission.ISSUE_CHANGE_STATUS,
            Permission.COMMENT_CREATE,
            Permission.LABEL_CREATE,
            Permission.LABEL_READ,
            Permission.WORKFLOW_STATE_READ,
            Permission.ATTACHMENT_CREATE,
        }
    ),
    WorkspaceRole.GUEST: frozenset(
        {
            Permission.WORKSPACE_VIEW,
            Permission.PROJECT_READ,
            Permission.ISSUE_READ,
            Permission.COMMENT_CREATE,
            Permission.LABEL_READ,
            Permission.WORKFLOW_STATE_READ,
            Permission.ATTACHMENT_CREATE,
        }
    ),
}

# Permissões concedidas a QUALQUER papel quando o chamador é o dono do recurso
# (`resource_owner_id == member.user_id`), além do que a matriz acima já
# concede pelo papel. Modela "excluir comentário/issue própria" sem precisar
# de uma segunda matriz por recurso: o papel decide o caso geral, a posse
# decide a exceção — mesma regra em `docs/07-security.md` §8.
OWNERSHIP_OVERRIDE_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.COMMENT_UPDATE,
        Permission.COMMENT_DELETE,
        Permission.ISSUE_DELETE,
        Permission.ATTACHMENT_DELETE,
    }
)


class PermissionService:
    """Único ponto de decisão de autorização do FlowDesk.

    Instanciado por requisição via DI (`get_permission_service`), sem estado
    próprio — toda decisão depende só dos argumentos recebidos, o que a torna
    trivialmente testável sem banco ou HTTP.
    """

    def can(
        self,
        *,
        member: WorkspaceMember,
        permission: Permission,
        resource_owner_id: uuid.UUID | None = None,
        granted_overrides: frozenset[Permission] = frozenset(),
        revoked_overrides: frozenset[Permission] = frozenset(),
    ) -> bool:
        """`granted_overrides`/`revoked_overrides` (Sprint 9.3, ADR-058) — o
        conjunto de `PermissionOverride` já resolvido para `member.role` neste
        workspace (via `WorkspaceContext`). Uma permissão revogada nunca cai no
        fallback de posse abaixo: se o workspace desligou `comment.delete` para
        `MEMBER`, a intenção é remover a ação por completo, inclusive sobre o
        próprio recurso — não apenas sobre o de terceiros.
        """
        if permission in revoked_overrides:
            return False
        if permission in granted_overrides or permission in ROLE_PERMISSIONS[member.role]:
            return True
        return (
            permission in OWNERSHIP_OVERRIDE_PERMISSIONS
            and resource_owner_id is not None
            and resource_owner_id == member.user_id
        )

    def require(
        self,
        *,
        member: WorkspaceMember,
        permission: Permission,
        resource_owner_id: uuid.UUID | None = None,
        granted_overrides: frozenset[Permission] = frozenset(),
        revoked_overrides: frozenset[Permission] = frozenset(),
    ) -> None:
        if self.can(
            member=member,
            permission=permission,
            resource_owner_id=resource_owner_id,
            granted_overrides=granted_overrides,
            revoked_overrides=revoked_overrides,
        ):
            return
        logger.warning(
            "permission_denied",
            user_id=str(member.user_id),
            workspace_id=str(member.workspace_id),
            role=member.role.value,
            permission=permission.value,
        )
        raise PermissionDeniedError()

    def can_manage_member(self, *, actor_role: WorkspaceRole, target_role: WorkspaceRole) -> bool:
        """Regra contextual de `docs/07-security.md` §8 ("Alterar papel de
        membro": ADMIN pode, exceto sobre um OWNER) — não expressável na
        matriz estática porque depende do papel do *alvo*, só conhecido depois
        que o service já buscou a `WorkspaceMember` a ser gerenciada.
        """
        if actor_role == WorkspaceRole.OWNER:
            return True
        if actor_role == WorkspaceRole.ADMIN:
            return target_role != WorkspaceRole.OWNER
        return False

    def require_can_manage_member(
        self, *, actor_role: WorkspaceRole, target_role: WorkspaceRole
    ) -> None:
        if self.can_manage_member(actor_role=actor_role, target_role=target_role):
            return
        logger.warning(
            "permission_denied",
            reason="cannot_manage_owner",
            actor_role=actor_role.value,
            target_role=target_role.value,
        )
        raise CannotManageOwnerError()


def get_permission_service() -> PermissionService:
    return PermissionService()


@dataclass(frozen=True)
class WorkspaceContext:
    """Resultado da etapa "Workspace Context" do fluxo de autorização —
    confirma que o workspace existe e que o chamador é membro dele antes de
    qualquer permissão específica ser avaliada. Não-membro e workspace
    inexistente colapsam no mesmo `WorkspaceNotFoundError` (404), mesmo
    racional anti-enumeration já usado em toda a feature de workspaces
    (`docs/07-security.md` §9.1).

    `granted_overrides`/`revoked_overrides` (Sprint 9.3, ADR-058): os
    `PermissionOverride` do workspace já resolvidos para `member.role` — vazios
    (`frozenset()`) no caso comum de nenhum override configurado.
    """

    workspace: Workspace
    member: WorkspaceMember
    granted_overrides: frozenset[Permission] = field(default_factory=frozenset)
    revoked_overrides: frozenset[Permission] = field(default_factory=frozenset)


async def get_workspace_context(
    workspace_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceContext:
    workspace_repo: WorkspaceRepositoryProtocol = WorkspaceRepository(session)

    workspace = await workspace_repo.get_by_id(workspace_id)
    if workspace is None:
        raise WorkspaceNotFoundError()

    member = await workspace_repo.get_member(workspace_id, current_user.id)
    if member is None:
        raise WorkspaceNotFoundError()

    override_repo = PermissionOverrideRepository(session)
    granted, revoked = await override_repo.get_role_overrides(workspace_id, member.role)

    return WorkspaceContext(
        workspace=workspace, member=member, granted_overrides=granted, revoked_overrides=revoked
    )


def require_permission(permission: Permission) -> Callable[..., Awaitable[WorkspaceMember]]:
    """Factory de dependency (`CLAUDE.md` §10): declarada na assinatura da
    rota (`Depends(require_permission(Permission.WORKSPACE_UPDATE))`), nunca
    um `if` manual no corpo dela. Resolve o `WorkspaceContext` e consulta o
    `PermissionService` antes do service layer ser chamado — se negado, a
    requisição nunca alcança a regra de negócio.

    Retorna a `WorkspaceMember` do chamador para o router reaproveitar sem uma
    segunda consulta (ex.: repassar `acting_member.role` ao service para uma
    checagem contextual adicional, como `require_can_manage_member`).
    """

    async def _require_permission(
        context: WorkspaceContext = Depends(get_workspace_context),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> WorkspaceMember:
        permission_service.require(
            member=context.member,
            permission=permission,
            granted_overrides=context.granted_overrides,
            revoked_overrides=context.revoked_overrides,
        )
        return context.member

    return _require_permission
