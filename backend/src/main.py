import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import src.db.models_registry  # noqa: F401
from src.core.config import get_settings
from src.core.exceptions import (
    FlowDeskError,
    flowdesk_exception_handler,
    http_exception_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
)
from src.core.health import run_health_checks
from src.core.logging import configure_logging, get_logger
from src.core.middleware import (
    AccessLogMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from src.features.attachments.router import router as attachments_router
from src.features.auth.router import router as auth_router
from src.features.comments.router import router as comments_router
from src.features.issues.router import router as issues_router
from src.features.labels.router import router as labels_router
from src.features.notifications.router import router as notifications_router
from src.features.projects.router import router as projects_router
from src.features.users.router import router as users_router
from src.features.workspaces.router import invitations_router
from src.features.workspaces.router import router as workspaces_router

settings = get_settings()
configure_logging(
    log_level=settings.log_level,
    json_output=settings.is_production,
    environment=settings.environment,
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.started_at = time.monotonic()
    logger.info("application_startup", environment=settings.environment)
    yield


app = FastAPI(
    title="FlowDesk API",
    version=settings.api_version,
    description="API do FlowDesk — gestão de issues e projetos para times de produto.",
    lifespan=lifespan,
)

# Ordem (docs/06-backend.md §5): CORS -> Security Headers -> Request ID -> Access Log
# -> Rate Limit -> rotas. Starlette empilha middlewares em ordem reversa de inserção —
# o último `add_middleware` chamado é o mais externo — então a ordem de chamada abaixo
# é o inverso da ordem de execução desejada.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-Request-ID"],
)

# Starlette tipa o handler para a classe base Exception; registrar por subtipo é o uso
# suportado e documentado, mas exige silenciar a variância de tipo aqui.
app.add_exception_handler(FlowDeskError, flowdesk_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(workspaces_router)
api_router.include_router(invitations_router)
api_router.include_router(projects_router)
api_router.include_router(issues_router)
api_router.include_router(labels_router)
api_router.include_router(comments_router)
api_router.include_router(attachments_router)
api_router.include_router(notifications_router)
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness check — usado por Docker/orquestrador para saber se o processo está de pé."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
async def health_ready(response: Response) -> dict[str, object]:
    """Readiness check — verifica se as dependências (banco, Redis, storage) respondem,
    não só se o processo está de pé (`/health`). 503 quando qualquer checagem falha, para
    que um orquestrador/load balancer pare de rotear tráfego para esta instância."""
    report = await run_health_checks()
    if report.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": report.status,
        "checks": {
            check.name: {
                "status": check.status,
                "latency_ms": check.latency_ms,
                "detail": check.detail,
            }
            for check in report.checks
        },
    }


@app.get("/version", tags=["system"])
async def version(request: Request) -> dict[str, object]:
    """Versão da API em execução, ambiente e tempo de atividade — útil para depurar qual
    build está no ar e detectar reinícios inesperados."""
    uptime_seconds = time.monotonic() - request.app.state.started_at
    return {
        "version": settings.api_version,
        "environment": settings.environment,
        "uptime_seconds": round(uptime_seconds, 3),
    }
