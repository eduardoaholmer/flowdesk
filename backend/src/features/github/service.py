import secrets
import uuid
from datetime import UTC, datetime

from src.core.authorization import PermissionService
from src.core.logging import get_logger
from src.core.permissions import Permission
from src.features.github.client import GitHubAppClientProtocol
from src.features.github.exceptions import (
    GitHubAuthorizationFailedError,
    GitHubConnectStateInvalidError,
    GitHubInstallationAlreadyConnectedError,
    GitHubInstallationNotAccessibleError,
    GitHubInstallationNotFoundError,
    GitHubInstallationPendingApprovalError,
    GitHubIntegrationNotConfiguredError,
)
from src.features.github.models import GitHubInstallation, GitHubWebhookOutcome
from src.features.github.repository import (
    GitHubConnectIntent,
    GitHubConnectStateRepositoryProtocol,
    GitHubInstallationRepositoryProtocol,
    GitHubWebhookDeliveryRepositoryProtocol,
)
from src.features.github.schemas import (
    GitHubConnectionStart,
    GitHubIntegrationStatus,
    GitHubWebhookDeliveryInput,
    GitHubWebhookResult,
)
from src.features.permissions.repository import PermissionOverrideRepositoryProtocol
from src.features.workspaces.exceptions import WorkspaceNotFoundError
from src.features.workspaces.repository import WorkspaceRepositoryProtocol

logger = get_logger(__name__)

CONNECT_STATE_TTL_SECONDS = 10 * 60
_SETUP_ACTION_REQUEST = "request"
_EVENT_INSTALLATION = "installation"
_EVENT_INSTALLATION_REPOSITORIES = "installation_repositories"
HANDLED_WEBHOOK_EVENTS = frozenset({_EVENT_INSTALLATION, _EVENT_INSTALLATION_REPOSITORIES})
# Motivo gravado em `github_webhook_deliveries.reason` quando a entrega é ignorada —
# a resposta para "o GitHub mandou e o FlowDesk ignorou por quê?".
_REASON_UNHANDLED_EVENT = "unhandled_event"
_REASON_UNHANDLED_ACTION = "unhandled_action"
_REASON_MISSING_INSTALLATION = "missing_installation"
_REASON_UNKNOWN_INSTALLATION = "unknown_installation"
# `installation_id` vai para uma coluna `BIGINT`; mais de 18 dígitos poderia
# estourar o tipo e virar um 500 em vez de um retorno de erro legível.
_MAX_INSTALLATION_ID_DIGITS = 18


class GitHubIntegrationService:
    def __init__(
        self,
        installation_repo: GitHubInstallationRepositoryProtocol,
        state_repo: GitHubConnectStateRepositoryProtocol,
        workspace_repo: WorkspaceRepositoryProtocol,
        override_repo: PermissionOverrideRepositoryProtocol,
        permission_service: PermissionService,
        client: GitHubAppClientProtocol | None,
    ) -> None:
        """`client` é `None` quando o GitHub App não está configurado neste ambiente
        (`Settings.github_app_configured`) — mesmo sinal de "provedor desligado" do
        dicionário de clients de `AuthService`."""
        self._installation_repo = installation_repo
        self._state_repo = state_repo
        self._workspace_repo = workspace_repo
        self._override_repo = override_repo
        self._permission_service = permission_service
        self._client = client

    async def get_status(self, workspace_id: uuid.UUID) -> GitHubIntegrationStatus:
        installations = await self._installation_repo.list_by_workspace(workspace_id)
        return GitHubIntegrationStatus(
            configured=self._client is not None, installations=installations
        )

    async def start_connection(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> GitHubConnectionStart:
        client = self._require_client()
        state = secrets.token_urlsafe(32)
        await self._state_repo.save(
            state,
            GitHubConnectIntent(workspace_id=workspace_id, user_id=user_id),
            CONNECT_STATE_TTL_SECONDS,
        )
        return GitHubConnectionStart(install_url=client.installation_url(state), state=state)

    async def complete_connection(
        self,
        *,
        state: str | None,
        browser_state: str | None,
        code: str | None,
        installation_id: str | None,
        setup_action: str | None,
    ) -> GitHubInstallation:
        """Retorno do GitHub depois da instalação (ADR-068). `browser_state` é o
        cookie gravado no navegador que chamou `connect`: sem ele, um atacante
        poderia gerar um `state` para o próprio workspace e fazer outra pessoa
        concluir a instalação da organização dela com esse link."""
        if not state or not browser_state or not secrets.compare_digest(state, browser_state):
            raise GitHubConnectStateInvalidError()
        intent = await self._state_repo.pop(state)
        if intent is None:
            raise GitHubConnectStateInvalidError()

        client = self._require_client()
        if setup_action == _SETUP_ACTION_REQUEST:
            raise GitHubInstallationPendingApprovalError()
        github_installation_id = _parse_installation_id(installation_id)
        if not code or github_installation_id is None:
            raise GitHubAuthorizationFailedError()

        # O `state` vale por até 10 minutos depois do `require_permission` do
        # `connect`; a permissão é conferida de novo para que uma remoção ou
        # rebaixamento nesse intervalo também valha aqui.
        await self._require_manage_integrations(intent)

        info = await client.find_user_installation(code, github_installation_id)
        if info is None:
            raise GitHubInstallationNotAccessibleError()

        existing = await self._installation_repo.get_active_by_installation_id(
            github_installation_id
        )
        if existing is not None and existing.workspace_id != intent.workspace_id:
            if await self._workspace_repo.get_by_id(existing.workspace_id) is not None:
                raise GitHubInstallationAlreadyConnectedError()
            # O workspace dono foi excluído sem desconectar antes; a instalação
            # ficaria presa a ele e a organização não conseguiria se conectar a
            # nenhum outro workspace.
            await self._installation_repo.soft_delete(existing.workspace_id, existing.id)
            existing = None
        if existing is not None:
            # Mesmo workspace: o dono só reconfigurou os repositórios no GitHub
            # (`setup_action=update`). Atualiza o que pode ter mudado, sem duplicar.
            existing.account_login = info.account_login
            existing.suspended_at = info.suspended_at
            return await self._installation_repo.update(existing)

        installation = await self._installation_repo.create(
            GitHubInstallation(
                workspace_id=intent.workspace_id,
                installation_id=info.installation_id,
                account_login=info.account_login,
                account_type=info.account_type,
                connected_by_id=intent.user_id,
                suspended_at=info.suspended_at,
            )
        )
        logger.info(
            "github_installation_connected",
            workspace_id=str(intent.workspace_id),
            user_id=str(intent.user_id),
            installation_id=info.installation_id,
        )
        return installation

    async def disconnect(self, workspace_id: uuid.UUID, installation_pk: uuid.UUID) -> None:
        installation = await self._installation_repo.get_by_id(workspace_id, installation_pk)
        if installation is None:
            raise GitHubInstallationNotFoundError()
        await self._installation_repo.soft_delete(workspace_id, installation_pk)
        logger.info(
            "github_installation_disconnected",
            workspace_id=str(workspace_id),
            installation_id=installation.installation_id,
        )

    def _require_client(self) -> GitHubAppClientProtocol:
        if self._client is None:
            raise GitHubIntegrationNotConfiguredError()
        return self._client

    async def _require_manage_integrations(self, intent: GitHubConnectIntent) -> None:
        if await self._workspace_repo.get_by_id(intent.workspace_id) is None:
            raise WorkspaceNotFoundError()
        member = await self._workspace_repo.get_member(intent.workspace_id, intent.user_id)
        if member is None:
            raise WorkspaceNotFoundError()
        granted, revoked = await self._override_repo.get_role_overrides(
            intent.workspace_id, member.role
        )
        self._permission_service.require(
            member=member,
            permission=Permission.WORKSPACE_MANAGE_INTEGRATIONS,
            granted_overrides=granted,
            revoked_overrides=revoked,
        )


class GitHubWebhookService:
    """Recebe as entregas do webhook já autenticadas (HMAC no router, ADR-069). Cada
    entrega é processada uma única vez: `claim` e o efeito acontecem na mesma
    transação, e um reenvio do mesmo `delivery_id` devolve o resultado da primeira
    vez sem repetir nada."""

    def __init__(
        self,
        installation_repo: GitHubInstallationRepositoryProtocol,
        delivery_repo: GitHubWebhookDeliveryRepositoryProtocol,
    ) -> None:
        self._installation_repo = installation_repo
        self._delivery_repo = delivery_repo

    async def handle(self, delivery: GitHubWebhookDeliveryInput) -> GitHubWebhookResult:
        payload = delivery.payload
        installation_id = payload.installation.id if payload.installation else None
        claimed = await self._delivery_repo.claim(
            delivery_id=delivery.delivery_id,
            event=delivery.event,
            action=payload.action,
            installation_id=installation_id,
        )
        if not claimed:
            existing = await self._delivery_repo.get(delivery.delivery_id)
            # `claim` só devolve `False` porque a linha já existe.
            assert existing is not None
            logger.info(
                "github_webhook_duplicate",
                delivery_id=delivery.delivery_id,
                github_event=delivery.event,
            )
            return GitHubWebhookResult(outcome=existing.outcome, duplicate=True)

        outcome, reason, workspace_id = await self._dispatch(delivery)
        await self._delivery_repo.finish(
            delivery.delivery_id, outcome=outcome, reason=reason, workspace_id=workspace_id
        )
        logger.info(
            "github_webhook_received",
            delivery_id=delivery.delivery_id,
            github_event=delivery.event,
            action=payload.action,
            installation_id=installation_id,
            workspace_id=str(workspace_id) if workspace_id else None,
            outcome=outcome.value,
            reason=reason,
        )
        return GitHubWebhookResult(outcome=outcome, duplicate=False)

    async def _dispatch(
        self, delivery: GitHubWebhookDeliveryInput
    ) -> tuple[GitHubWebhookOutcome, str | None, uuid.UUID | None]:
        if delivery.event not in HANDLED_WEBHOOK_EVENTS:
            return GitHubWebhookOutcome.IGNORED, _REASON_UNHANDLED_EVENT, None
        payload = delivery.payload
        if payload.installation is None:
            return GitHubWebhookOutcome.IGNORED, _REASON_MISSING_INSTALLATION, None
        installation = await self._installation_repo.get_active_by_installation_id(
            payload.installation.id
        )
        if installation is None:
            # Instalado no GitHub mas nunca conectado (ou já desconectado) aqui.
            return GitHubWebhookOutcome.IGNORED, _REASON_UNKNOWN_INSTALLATION, None

        workspace_id = installation.workspace_id
        if delivery.event == _EVENT_INSTALLATION_REPOSITORIES:
            # Só registrado nesta sprint (ADR-069): nenhum dado do FlowDesk depende
            # ainda de quais repositórios a instalação enxerga.
            return GitHubWebhookOutcome.PROCESSED, None, workspace_id

        if payload.action == "deleted":
            await self._installation_repo.soft_delete(workspace_id, installation.id)
            logger.info(
                "github_installation_disconnected",
                workspace_id=str(workspace_id),
                installation_id=installation.installation_id,
                source="github",
            )
        elif payload.action == "suspend":
            installation.suspended_at = payload.installation.suspended_at or datetime.now(UTC)
            await self._installation_repo.update(installation)
        elif payload.action == "unsuspend":
            installation.suspended_at = None
            await self._installation_repo.update(installation)
        else:
            return GitHubWebhookOutcome.IGNORED, _REASON_UNHANDLED_ACTION, workspace_id
        return GitHubWebhookOutcome.PROCESSED, None, workspace_id


def _parse_installation_id(raw: str | None) -> int | None:
    """O valor chega da query string da navegação de volta do GitHub, então é
    texto livre até prova em contrário."""
    if not raw or not raw.isascii() or not raw.isdigit() or len(raw) > _MAX_INSTALLATION_ID_DIGITS:
        return None
    return int(raw)
