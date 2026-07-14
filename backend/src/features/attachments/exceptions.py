from src.core.exceptions import NotFoundError, ValidationError


class AttachmentNotFoundError(NotFoundError):
    code = "attachment_not_found"
    message = "Anexo não encontrado."


class AttachmentTooLargeError(ValidationError):
    code = "attachment_too_large"
    message = "O arquivo excede o tamanho máximo permitido."


class AttachmentTypeNotAllowedError(ValidationError):
    code = "attachment_type_not_allowed"
    message = "Este tipo de arquivo não é permitido."
