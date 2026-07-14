from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)


class FlowDeskError(Exception):
    """Base de toda exceção de domínio. Nunca lançada diretamente — ver CLAUDE.md §7."""

    code: str = "internal_error"
    message: str = "Erro interno."
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None, *, details: object = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details


class NotFoundError(FlowDeskError):
    code = "not_found"
    message = "Recurso não encontrado."
    status_code = status.HTTP_404_NOT_FOUND


class ValidationError(FlowDeskError):
    code = "validation_error"
    message = "Dados inválidos."
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ConflictError(FlowDeskError):
    code = "conflict"
    message = "Conflito com o estado atual do recurso."
    status_code = status.HTTP_409_CONFLICT


class PermissionDeniedError(FlowDeskError):
    code = "permission_denied"
    message = "Você não tem permissão para executar esta ação."
    status_code = status.HTTP_403_FORBIDDEN


class AuthenticationError(FlowDeskError):
    code = "authentication_error"
    message = "Não autenticado."
    status_code = status.HTTP_401_UNAUTHORIZED


class RateLimitedError(FlowDeskError):
    code = "rate_limited"
    message = "Muitas requisições. Tente novamente mais tarde."
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class InvalidTokenError(AuthenticationError):
    """Bearer ausente, malformado, expirado, ou apontando para usuário inexistente/desativado.

    Todas essas causas colapsam no mesmo `code` deliberadamente — não damos ao
    cliente informação suficiente para distinguir "seu token expirou" de "essa
    conta não existe mais" (`docs/07-security.md` §10, anti-enumeration).
    """

    code = "invalid_token"
    message = "Token inválido ou expirado."


def error_response(
    *, code: str, message: str, status_code: int, details: object = None
) -> JSONResponse:
    """Constrói o envelope de erro padrão (CLAUDE.md §8) fora do fluxo de exceções.

    Usado pelo handler global abaixo e por qualquer middleware (ex.: rate limit)
    que precise responder antes de o request alcançar o `ExceptionMiddleware` do
    Starlette — que não intercepta com segurança exceções levantadas em
    middlewares `BaseHTTPMiddleware` de terceiros.
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


async def flowdesk_exception_handler(request: Request, exc: FlowDeskError) -> JSONResponse:
    """Handler global: traduz exceção de domínio -> envelope de erro padrão (CLAUDE.md §8)."""
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error("unhandled_domain_error", code=exc.code, path=request.url.path)
    else:
        logger.info("domain_error", code=exc.code, path=request.url.path)

    return error_response(
        code=exc.code, message=exc.message, status_code=exc.status_code, details=exc.details
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Rede de segurança para exceções não mapeadas: nunca vaza detalhe interno ao cliente."""
    logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "Erro interno. Tente novamente mais tarde.",
                "details": None,
            }
        },
    )
