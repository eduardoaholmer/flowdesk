import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import request_id_ctx

REQUEST_ID_HEADER = "X-Request-ID"


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
