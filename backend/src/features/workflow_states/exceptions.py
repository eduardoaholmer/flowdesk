from src.core.exceptions import ConflictError, NotFoundError


class WorkflowStateNotFoundError(NotFoundError):
    code = "workflow_state_not_found"
    message = "Status não encontrado."


class WorkflowStateNameTakenError(ConflictError):
    code = "workflow_state_name_taken"
    message = "Já existe um status com este nome neste workspace."


class WorkflowStateHasIssuesError(ConflictError):
    """Levantada quando o chamador tenta excluir um status com issues vinculadas
    sem informar `reassign_to_id` — carrega a contagem em `details` para o
    frontend decidir se pede confirmação/reatribuição ao usuário."""

    code = "workflow_state_has_issues"
    message = "Este status tem issues vinculadas. Informe para qual status reatribuí-las."


class CannotDeleteLastWorkflowStateError(ConflictError):
    code = "cannot_delete_last_workflow_state"
    message = "O workspace precisa de ao menos um status."


class InvalidReassignTargetError(ConflictError):
    code = "invalid_reassign_target"
    message = "O status de destino da reatribuição é inválido."
