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


class InvalidParentIssueError(ConflictError):
    """Sprint 9.4 (ADR-059): qualquer violação da regra "só um nível de
    sub-issues" — auto-referência, pai que já é filho, pai que já tem filhos,
    ou a própria issue que já tem filhos tentando virar filha de outra."""

    code = "invalid_parent_issue"
    message = "Vínculo de sub-issue inválido."


class IssueHasSubIssuesError(ConflictError):
    code = "issue_has_subissues"
    message = "Esta issue tem sub-issues vinculadas. Remova o vínculo ou exclua-as antes."
