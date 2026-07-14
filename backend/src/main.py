from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.db.models_registry  # noqa: F401
from src.core.config import get_settings
from src.core.exceptions import (
    FlowDeskError,
    flowdesk_exception_handler,
    unhandled_exception_handler,
)
from src.core.logging import configure_logging, get_logger
from src.core.middleware import RateLimitMiddleware, RequestIDMiddleware
from src.features.auth.router import router as auth_router
from src.features.projects.router import router as projects_router
from src.features.users.router import router as users_router
from src.features.workspaces.router import invitations_router
from src.features.workspaces.router import router as workspaces_router

settings = get_settings()
configure_logging(log_level=settings.log_level, json_output=settings.is_production)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application_startup", environment=settings.environment)
    yield


app = FastAPI(
    title="FlowDesk API",
    version=settings.api_version,
    description="API do FlowDesk — gestão de issues e projetos para times de produto.",
    lifespan=lifespan,
)

# Ordem (docs/06-backend.md §5): CORS -> Request ID -> Rate Limit -> rotas.
# Starlette empilha middlewares em ordem reversa de inserção — o último
# `add_middleware` chamado é o mais externo — então a ordem de chamada abaixo é
# o inverso da ordem de execução desejada.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Starlette tipa o handler para a classe base Exception; registrar por subtipo é o uso
# suportado e documentado, mas exige silenciar a variância de tipo aqui.
app.add_exception_handler(FlowDeskError, flowdesk_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(workspaces_router)
api_router.include_router(invitations_router)
api_router.include_router(projects_router)
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness check — usado por Docker/orquestrador para saber se o processo está de pé."""
    return {"status": "ok"}


@app.get("/version", tags=["system"])
async def version() -> dict[str, str]:
    """Versão da API em execução e ambiente — útil para depurar qual build está no ar."""
    return {"version": settings.api_version, "environment": settings.environment}
