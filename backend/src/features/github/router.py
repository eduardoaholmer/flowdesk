import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import RedirectResponse

from src.core.authorization import require_permission
from src.core.config import Settings, get_settings
from src.core.exceptions import FlowDeskError
from src.core.metrics import increment_counter
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.features.github.dependencies import (
    DELIVERY_HEADER,
    EVENT_HEADER,
    get_github_integration_service,
    get_github_pull_request_link_service,
    get_github_webhook_service,
    verify_github_webhook,
)
from src.features.github.schemas import (
    GitHubConnectResponse,
    GitHubIntegrationResponse,
    GitHubPullRequestLinkResponse,
    GitHubStatusAutomationResponse,
    GitHubStatusAutomationUpdateRequest,
    GitHubWebhookDeliveryInput,
    GitHubWebhookResponse,
)
from src.features.github.service import (
    CONNECT_STATE_TTL_SECONDS,
    HANDLED_WEBHOOK_EVENTS,
    GitHubIntegrationService,
    GitHubPullRequestLinkService,
    GitHubWebhookService,
)
from src.features.workspaces.models import WorkspaceMember

router = APIRouter(prefix="/workspaces/{workspace_id}/integrations/github", tags=["github"])
setup_router = APIRouter(prefix="/integrations/github", tags=["github"])
webhook_router = APIRouter(prefix="/webhooks/github", tags=["github"])
issue_links_router = APIRouter(
    prefix="/workspaces/{workspace_id}/issues/{issue_id}/github-links", tags=["github"]
)

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


@router.get("/automations", response_model=DataEnvelope[list[GitHubStatusAutomationResponse]])
async def list_github_automations(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        require_permission(Permission.WORKSPACE_MANAGE_INTEGRATIONS)
    ),
    service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> DataEnvelope[list[GitHubStatusAutomationResponse]]:
    automations = await service.list_automations(workspace_id)
    return DataEnvelope(
        data=[GitHubStatusAutomationResponse.model_validate(rule) for rule in automations]
    )


@router.put("/automations", response_model=DataEnvelope[list[GitHubStatusAutomationResponse]])
async def set_github_automation(
    workspace_id: uuid.UUID,
    payload: GitHubStatusAutomationUpdateRequest,
    _member: WorkspaceMember = Depends(
        require_permission(Permission.WORKSPACE_MANAGE_INTEGRATIONS)
    ),
    service: GitHubIntegrationService = Depends(get_github_integration_service),
) -> DataEnvelope[list[GitHubStatusAutomationResponse]]:
    """Grava a regra de um evento (`target_state_id: null` = sem ação) e devolve as
    quatro, como o `PUT` de overrides de permissão devolve a matriz inteira."""
    automations = await service.set_automation(workspace_id, payload.event, payload.target_state_id)
    return DataEnvelope(
        data=[GitHubStatusAutomationResponse.model_validate(rule) for rule in automations]
    )


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


@webhook_router.post("", response_model=DataEnvelope[GitHubWebhookResponse])
async def receive_github_webhook(
    body: bytes = Depends(verify_github_webhook),
    delivery_id: str | None = Header(default=None, alias=DELIVERY_HEADER),
    event: str | None = Header(default=None, alias=EVENT_HEADER),
    service: GitHubWebhookService = Depends(get_github_webhook_service),
) -> DataEnvelope[GitHubWebhookResponse]:
    """Entregas do webhook do GitHub App (ADR-069). Fora de `/workspaces/{id}` e sem
    JWT: o GitHub não conhece o workspace, e quem autentica é o HMAC do corpo
    (`verify_github_webhook`). O workspace sai do `installation.id` do corpo já
    verificado.

    Evento válido que não interessa responde 200 com `outcome=IGNORED`: um 4xx faria
    o GitHub marcar a entrega como falha sem nenhum benefício."""
    delivery = GitHubWebhookDeliveryInput.parse(delivery_id=delivery_id, event=event, body=body)
    result = await service.handle(delivery)
    # O rótulo do evento é limitado aos tratados: cada valor distinto vira uma chave
    # nova no Redis (`increment_counter`).
    event_label = delivery.event if delivery.event in HANDLED_WEBHOOK_EVENTS else "other"
    outcome_label = "DUPLICATE" if result.duplicate else result.outcome.value
    await increment_counter(f"github_webhook.{event_label}.{outcome_label}")
    return DataEnvelope(
        data=GitHubWebhookResponse(outcome=result.outcome, duplicate=result.duplicate)
    )


@issue_links_router.get("", response_model=DataEnvelope[list[GitHubPullRequestLinkResponse]])
async def list_issue_github_links(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: GitHubPullRequestLinkService = Depends(get_github_pull_request_link_service),
) -> DataEnvelope[list[GitHubPullRequestLinkResponse]]:
    """Pull requests que citam a issue (Sprint 10.3). Mesma permissão de ler a issue:
    o vínculo só expõe o que o GitHub já mostra no PR para quem enxerga a issue."""
    links = await service.list_for_issue(workspace_id, issue_id)
    return DataEnvelope(data=[GitHubPullRequestLinkResponse.model_validate(link) for link in links])
