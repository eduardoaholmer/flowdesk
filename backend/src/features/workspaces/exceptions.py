from src.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError


class WorkspaceNotFoundError(NotFoundError):
    """Cobre workspace inexistente **e** workspace existente do qual o usuário não
    é membro — o mesmo `code`/status para os dois casos, nunca confirmando a um
    não-membro que o recurso existe (`docs/07-security.md` §10, mesmo racional
    anti-enumeration já usado em auth).
    """

    code = "workspace_not_found"
    message = "Workspace não encontrado."


class SlugTakenError(ConflictError):
    code = "slug_taken"
    message = "Este slug já está em uso."


class AlreadyMemberError(ConflictError):
    code = "already_member"
    message = "Este usuário já é membro do workspace."


class InvitationAlreadyPendingError(ConflictError):
    code = "invitation_already_pending"
    message = "Já existe um convite pendente para este e-mail."


class InvitationNotFoundError(NotFoundError):
    code = "invitation_not_found"
    message = "Convite não encontrado."


class InvitationExpiredError(ConflictError):
    """Também cobre convite já aceito — ambos são "não pode mais ser usado",
    mesmo racional de colapsar causas em um único `code` (`docs/07-security.md`).
    """

    code = "invitation_expired"
    message = "Este convite expirou ou já foi utilizado."


class InvitationEmailMismatchError(PermissionDeniedError):
    code = "invitation_email_mismatch"
    message = "Este convite foi emitido para outro e-mail."


class CannotLeaveAsSoleOwnerError(ConflictError):
    code = "sole_owner_cannot_leave"
    message = "Transfira a propriedade do workspace antes de sair — você é o único OWNER."


class MemberNotFoundError(NotFoundError):
    code = "member_not_found"
    message = "Membro não encontrado."


class CannotManageOwnMembershipError(ConflictError):
    """`PATCH`/`DELETE .../members/{member_id}` são ações administrativas sobre
    *outro* membro — gerenciar a própria associação (sair, trocar o próprio
    papel) passa por `DELETE .../members/me` ou por
    `POST .../members/{member_id}/transfer-ownership` (Sprint 17.1/M6).
    """

    code = "cannot_manage_own_membership"
    message = "Use o endpoint de sair do workspace para alterar sua própria associação."


class CannotManageOwnerError(PermissionDeniedError):
    """Regra contextual de `docs/07-security.md` §8: um ADMIN pode gerenciar
    qualquer membro, exceto outro OWNER — evita que um ADMIN rebaixe ou remova
    o dono do workspace.
    """

    code = "cannot_manage_owner"
    message = "Não é possível alterar ou remover um OWNER."


class CannotTransferOwnershipToSelfError(ConflictError):
    code = "cannot_transfer_ownership_to_self"
    message = "Você já é o OWNER deste workspace."
