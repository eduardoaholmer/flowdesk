from src.core.exceptions import NotFoundError


class CommentNotFoundError(NotFoundError):
    code = "comment_not_found"
    message = "Comentário não encontrado."
