from src.core.exceptions import ConflictError, NotFoundError


class LabelNotFoundError(NotFoundError):
    code = "label_not_found"
    message = "Label não encontrada."


class LabelNameTakenError(ConflictError):
    code = "label_name_taken"
    message = "Já existe uma label com este nome neste workspace."
