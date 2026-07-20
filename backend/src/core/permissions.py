import enum


class Permission(enum.StrEnum):
    """Catálogo central de permissões do FlowDesk (Sprint 5 — RBAC).

    Toda decisão de autorização referencia um destes valores — nunca uma string
    solta espalhada por routers/services (`CLAUDE.md` §10). Adicionar uma
    permissão nova é só acrescentar um membro aqui e posicioná-lo em
    `core/authorization.py` (`ROLE_PERMISSIONS`/`OWNERSHIP_OVERRIDE_PERMISSIONS`)
    — nenhum outro arquivo do sistema precisa mudar para que a permissão exista
    e seja resolvível pelo `PermissionService`.

    Nomeadas por agregado de domínio, não por rota HTTP: várias rotas podem
    consultar a mesma permissão (ex.: `GET .../invitations` e
    `POST .../invitations` compartilham `WORKSPACE_INVITE`) quando a regra de
    negócio de fato exige o mesmo papel para ambas.
    """

    WORKSPACE_VIEW = "workspace.view"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_DELETE = "workspace.delete"
    WORKSPACE_INVITE = "workspace.invite"
    WORKSPACE_TRANSFER_OWNERSHIP = "workspace.transfer_ownership"

    MEMBER_REMOVE = "member.remove"
    MEMBER_UPDATE_ROLE = "member.update_role"

    PROJECT_CREATE = "project.create"
    PROJECT_READ = "project.read"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"

    ISSUE_CREATE = "issue.create"
    ISSUE_READ = "issue.read"
    ISSUE_UPDATE = "issue.update"
    ISSUE_DELETE = "issue.delete"
    ISSUE_ASSIGN = "issue.assign"
    ISSUE_CHANGE_STATUS = "issue.change_status"

    COMMENT_CREATE = "comment.create"
    COMMENT_UPDATE = "comment.update"
    COMMENT_DELETE = "comment.delete"

    LABEL_CREATE = "label.create"
    LABEL_READ = "label.read"
    LABEL_UPDATE = "label.update"
    LABEL_DELETE = "label.delete"

    ATTACHMENT_CREATE = "attachment.create"
    ATTACHMENT_DELETE = "attachment.delete"
