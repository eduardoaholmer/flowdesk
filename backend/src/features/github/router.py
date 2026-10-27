import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse

from src.core.authorization import require_permission
from src.core.config import Settings, get_settings
from src.core.exceptions import FlowDeskError
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.features.github.dependencies import get_github_integration_service
from src.features.github.schemas import GitHubConnectResponse, GitHubIntegrationResponse
from src.features.github.service import CONNECT_STATE_TTL_SECONDS, GitHubIntegrationService
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/integrations/github", tags=["github"])
setup_router = APIRouter(prefix="/integrations/github", tags=["github"])

CONNECT_STATE_COOKIE_NAME = "github_connect_state"
# Cobre só a rota de retorno (`setup_router`): o cookie é gravado pela resposta do
# `connect` (outro caminho) e só precisa voltar na navegação vinda do GitHub.
CONNECT_STATE_COOKIE_PATH = "/api/v1/integrations/github"


@router.get("", response_model=DataEnvelope[GitHubIntegrationResponse])
async def get_github_integration(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        require_permission(Permission.WORKSPACE_MANAGE_INTEGRATIONS)
    ),
    service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> DataEnvelope[GitHubIntegrationResponse]:
    integration_status = await service.get_status(workspace_id)
    return DataEnvelope(data=GitHubIntegrationResponse.from_status(integration_status))


@router.post("/connect", response_model=DataEnvelope[GitHubConnectResponse])
async def connect_github(
    workspace_id: uuid.UUID,
    response: Response,
    member: WorkspaceMember = Depends(require_permission(Permission.WORKSPACE_MANAGE_INTEGRATIONS)),
    service: GitHubIntegrationService = Depends(get_github_integration_service),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[GitHubConnectResponse]:
    """Devolve a URL de instalação do GitHub App para o SPA navegar até ela. Não é
    um redirect direto: a navegação de página inteira não levaria o access token,
    que só existe em memória no frontend (`CLAUDE.md` §11).

    O mesmo `state` vai num cookie `HttpOnly` deste navegador; `SameSite=Lax`
    porque ele precisa voltar na navegação de nível superior vinda de github.com,
    mesmo racional do `oauth_state` do login social (ADR-061)."""
    connection = await service.start_connection(workspace_id, member.user_id)
    response.set_cookie(
        CONNECT_STATE_COOKIE_NAME,
        connection.state,
        max_age=CONNECT_STATE_TTL_SECONDS,
        path=CONNECT_STATE_COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return DataEnvelope(data=GitHubConnectResponse(install_url=connection.install_url))


@router.delete("/installations/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_github_installation(
    workspace_id: uuid.UUID,
    installation_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        require_permission(Permission.WORKSPACE_MANAGE_INTEGRATIONS)
    ),
    service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> None:
    await service.disconnect(workspace_id, installation_id)


@setup_router.get("/setup")
async def complete_github_setup(
    request: Request,
    state: str | None = None,
    code: str | None = None,
    installation_id: str | None = None,
    setup_action: str | None = None,
    service: GitHubIntegrationService = Depends(get_github_integration_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Retorno do GitHub depois da instalação. Sem JWT: quem chega aqui é o
    navegador numa navegação de página inteira, e a identidade vem do `state`
    gravado no servidor pelo `connect`, conferido contra o cookie deste navegador.

    Mesma exceção documentada dos callbacks de login social (ADR-061/ADR-068): a
    exceção de domínio é capturada aqui e vira um redirect para a SPA com o `code`
    do erro, em vez de um JSON cru numa aba do navegador."""
    callback_url = f"{settings.frontend_base_url}/integrations/github/callback"
    try:
        await service.complete_connection(
            state=state,
            browser_state=request.cookies.get(CONNECT_STATE_COOKIE_NAME),
            code=code,
            installation_id=installation_id,
            setup_action=setup_action,
        )
    except FlowDeskError as exc:
        redirect = RedirectResponse(
            f"{callback_url}?{urlencode({'error': exc.code})}",
            status_code=status.HTTP_302_FOUND,
        )
    else:
        redirect = RedirectResponse(callback_url, status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(CONNECT_STATE_COOKIE_NAME, path=CONNECT_STATE_COOKIE_PATH)
    return redirect
