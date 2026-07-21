from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class ProjectNotFoundError(NotFoundError):
    code = "project_not_found"
    message = "Projeto não encontrado."


class ProjectSlugTakenError(ConflictError):
    code = "project_slug_taken"
    message = "Este slug já está em uso neste workspace."


class ProjectKeyTakenError(ConflictError):
    code = "project_key_taken"
    message = "Esta key já está em uso neste workspace."


class ProjectMemberNotInWorkspaceError(ValidationError):
    """O usuário precisa ser membro do workspace para ser vinculado a um projeto:
    membership de projeto é informativa (`ProjectMember`), mas só faz sentido
    para quem já pertence ao tenant — evita também que a FK `RESTRICT` para
    `users.id` estoure como 500 diante de um `user_id` arbitrário.
    """

    code = "project_member_not_in_workspace"
    message = "O usuário não é membro deste workspace."


class ProjectNameTakenError(ConflictError):
    code = "project_name_taken"
    message = "Já existe um projeto com este nome neste workspace."


class ProjectAlreadyArchivedError(ConflictError):
    code = "project_already_archived"
    message = "Este projeto já está arquivado."


class ProjectNotArchivedError(ConflictError):
    code = "project_not_archived"
    message = "Este projeto não está arquivado."


class ProjectHasActiveIssuesError(ConflictError):
    """Espelha em nível de service a mesma política já expressa no schema via
    `issues.project_id` -> `projects.id` `ON DELETE RESTRICT` — como a exclusão
    de projeto é soft delete (não dispara a FK do banco), esta checagem replica
    a mesma regra de integridade explicitamente (`CLAUDE.md` §6, `docs/09-decision-log.md`).
    """

    code = "project_has_active_issues"
    message = "Não é possível excluir um projeto com issues ativas vinculadas."
