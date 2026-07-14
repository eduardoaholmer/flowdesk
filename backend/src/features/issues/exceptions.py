from src.core.exceptions import ConflictError, NotFoundError


class IssueNotFoundError(NotFoundError):
    code = "issue_not_found"
    message = "Issue não encontrada."


class IssueVersionConflictError(ConflictError):
    """`If-Match` divergente do `version` atual da issue — concorrência
    otimista (docs/03-database.md §3), nunca "last write wins" silencioso.
    """

    code = "version_conflict"
    message = "Esta issue foi modificada por outra pessoa. Recarregue e tente novamente."


class IssueLabelAlreadyAppliedError(ConflictError):
    code = "issue_label_already_applied"
    message = "Esta label já está aplicada nesta issue."
