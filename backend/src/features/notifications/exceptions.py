from src.core.exceptions import NotFoundError


class NotificationNotFoundError(NotFoundError):
    code = "notification_not_found"
    message = "Notificação não encontrada."
