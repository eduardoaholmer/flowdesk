from src.core.exceptions import ConflictError, NotFoundError


class ProjectNotFoundError(NotFoundError):
    code = "project_not_found"
    message = "Projeto não encontrado."


class ProjectSlugTakenError(ConflictError):
    code = "project_slug_taken"
    message = "Este slug já está em uso neste workspace."


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
