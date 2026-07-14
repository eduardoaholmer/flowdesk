import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import get_settings
from src.core.exceptions import InvalidTokenError, error_response
from src.core.logging import request_id_ctx
from src.core.rate_limit import check_rate_limit
from src.core.security import decode_access_token, hash_refresh_token

REQUEST_ID_HEADER = "X-Request-ID"

_API_PREFIX = "/api/v1"
_LOGIN_REGISTER_PATHS = {f"{_API_PREFIX}/auth/login", f"{_API_PREFIX}/auth/register"}
_REFRESH_PATH = f"{_API_PREFIX}/auth/refresh"
_LOGIN_REGISTER_LIMIT = 5
_REFRESH_LIMIT = 10
_GENERAL_LIMIT = 300
_WINDOW_SECONDS = 60


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Gera (ou propaga) um request_id e o disponibiliza para todo log da requisição.

    Aceitar um X-Request-ID já enviado pelo cliente permite rastrear uma requisição
    ponta a ponta quando o chamador é outro serviço/proxy que já gerou o seu próprio.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = self._resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @staticmethod
    def _resolve_request_id(header_value: str | None) -> str:
        """Só reaproveita o request_id do cliente se for um UUID válido.

        Um valor arbitrário aceito sem validação entraria direto nos logs
        estruturados, permitindo injeção/spoofing de log por quem chama a API.
        """
        if header_value is not None:
            try:
                return str(uuid.UUID(header_value))
            except ValueError:
                pass
        return str(uuid.uuid4())


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Janela deslizante via Redis, antes de qualquer lógica de negócio
    (docs/06-backend.md §5, docs/07-security.md §6):

    - `/auth/login`, `/auth/register`: 5/min por IP (mitiga força bruta/enumeration).
    - `/auth/refresh`: 10/min pela identidade da sessão (hash do cookie de refresh
      — a identidade do usuário só é conhecida após consulta ao banco, então
      chegar lá primeiro derrotaria o propósito de limitar antes de tocar o banco;
      ver ADR-008), com IP como fallback se o cookie não vier.
    - Demais rotas de `/api/v1`: 300/min por usuário, quando um Bearer decodificável
      está presente (best-effort — um token inválido aqui simplesmente não limita,
      a rejeição de fato é responsabilidade de `get_current_user`).

    Responde 429 diretamente (não levanta `RateLimitedError`): exceções levantadas
    dentro de um `BaseHTTPMiddleware` não passam de forma confiável pelo
    `ExceptionMiddleware` do Starlette, que fica abaixo dos middlewares de usuário
    na pilha.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rule = self._resolve_rule(request)
        if rule is not None:
            key, limit = rule
            result = await check_rate_limit(key, limit=limit, window_seconds=_WINDOW_SECONDS)
            if not result.allowed:
                response = error_response(
                    code="rate_limited",
                    message="Muitas requisições. Tente novamente mais tarde.",
                    status_code=429,
                )
                response.headers["Retry-After"] = str(result.retry_after_seconds)
                return response

        return await call_next(request)

    @staticmethod
    def _resolve_rule(request: Request) -> tuple[str, int] | None:
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        if request.method == "POST" and path in _LOGIN_REGISTER_PATHS:
            return f"ip:{client_ip}:{path}", _LOGIN_REGISTER_LIMIT

        if request.method == "POST" and path == _REFRESH_PATH:
            refresh_cookie = request.cookies.get("refresh_token")
            identity = hash_refresh_token(refresh_cookie) if refresh_cookie else client_ip
            return f"refresh:{identity}", _REFRESH_LIMIT

        if path.startswith(_API_PREFIX):
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header[len("bearer ") :]
                try:
                    claims = decode_access_token(token, get_settings())
                except InvalidTokenError:
                    return None
                return f"user:{claims.sub}", _GENERAL_LIMIT

        return None
