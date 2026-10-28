import secrets
import uuid
from collections.abc import Sequence
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
from src.features.github.identifiers import extract_issue_numbers
from src.features.github.models import (
    GitHubAutomationEvent,
    GitHubInstallation,
    GitHubPullRequestLink,
    GitHubPullRequestState,
    GitHubWebhookOutcome,
)
from src.features.github.repository import (
    GitHubConnectIntent,
    GitHubConnectStateRepositoryProtocol,
    GitHubInstallationRepositoryProtocol,
    GitHubPullRequestLinkRepositoryProtocol,
    GitHubSenderRepositoryProtocol,
    GitHubStatusAutomationRepositoryProtocol,
    GitHubWebhookDeliveryRepositoryProtocol,
)
from src.features.github.schemas import (
    PULL_REQUEST_EVENT,
    GitHubConnectionStart,
    GitHubIntegrationStatus,
    GitHubPullRequestEventPayload,
    GitHubSenderRef,
    GitHubStatusAutomationView,
    GitHubWebhookDeliveryInput,
    GitHubWebhookResult,
)
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.models import ActivityActorSource, Issue
from src.features.issues.repository import IssueRepositoryProtocol
from src.features.issues.schemas import AutomationActor
from src.features.issues.service import IssueService
from src.features.permissions.repository import PermissionOverrideRepositoryProtocol
from src.features.workflow_states.exceptions import WorkflowStateNotFoundError
from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory
from src.features.workflow_states.repository import WorkflowStateRepositoryProtocol
from src.features.workspaces.exceptions import WorkspaceNotFoundError
from src.features.workspaces.repository import WorkspaceRepositoryProtocol

logger = get_logger(__name__)

CONNECT_STATE_TTL_SECONDS = 10 * 60
_SETUP_ACTION_REQUEST = "request"
_EVENT_INSTALLATION = "installation"
_EVENT_INSTALLATION_REPOSITORIES = "installation_repositories"
HANDLED_WEBHOOK_EVENTS = frozenset(
    {_EVENT_INSTALLATION, _EVENT_INSTALLATION_REPOSITORIES, PULL_REQUEST_EVENT}
)
# Ações de PR que podem mudar quais issues ele cita (título, corpo) ou o estado
# mostrado ao lado do vínculo. As demais (`labeled`, `assigned`, `synchronize`...)
# não mexem em nada que o FlowDesk guarda.
_PULL_REQUEST_ACTIONS = frozenset(
    {"opened", "reopened", "edited", "ready_for_review", "converted_to_draft", "closed"}
)
# Ações em que o PR muda de situação: a regra correspondente vale para todas as
# issues que ele cita. Em `edited` a situação não muda; a regra só vale para as
# issues que o PR passou a citar agora (ADR-075).
_STATE_CHANGE_ACTIONS = frozenset(
    {"opened", "reopened", "ready_for_review", "converted_to_draft", "closed"}
)
_AUTOMATION_EVENT_BY_STATE = {
    GitHubPullRequestState.DRAFT: GitHubAutomationEvent.PR_DRAFT,
    GitHubPullRequestState.OPEN: GitHubAutomationEvent.PR_OPEN,
    GitHubPullRequestState.MERGED: GitHubAutomationEvent.PR_MERGED,
    GitHubPullRequestState.CLOSED: GitHubAutomationEvent.PR_CLOSED,
}
_GITHUB_ACTOR_NAME = "GitHub"
# Motivo gravado em `github_webhook_deliveries.reason` quando a entrega é ignorada —
# a resposta para "o GitHub mandou e o FlowDesk ignorou por quê?".
_REASON_UNHANDLED_EVENT = "unhandled_event"
_REASON_UNHANDLED_ACTION = "unhandled_action"
_REASON_MISSING_INSTALLATION = "missing_installation"
_REASON_UNKNOWN_INSTALLATION = "unknown_installation"
_REASON_NO_ISSUE_REFERENCE = "no_issue_reference"
_REASON_STALE_EVENT = "stale_event"
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
        automation_repo: GitHubStatusAutomationRepositoryProtocol,
        workflow_state_repo: WorkflowStateRepositoryProtocol,
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
        self._automation_repo = automation_repo
        self._workflow_state_repo = workflow_state_repo
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
        await self._ensure_default_automations(intent.workspace_id)
        logger.info(
            "github_installation_connected",
            workspace_id=str(intent.workspace_id),
            user_id=str(intent.user_id),
            installation_id=info.installation_id,
        )
        return installation

    async def list_automations(self, workspace_id: uuid.UUID) -> list[GitHubStatusAutomationView]:
        """Uma entrada por evento, sempre na mesma ordem; evento sem regra gravada
        (workspace que nunca conectou o GitHub) aparece como "sem ação"."""
        stored = {
            rule.event: rule.target_state_id
            for rule in await self._automation_repo.list_by_workspace(workspace_id)
        }
        return [
            GitHubStatusAutomationView(event=event, target_state_id=stored.get(event))
            for event in GitHubAutomationEvent
        ]

    async def set_automation(
        self,
        workspace_id: uuid.UUID,
        event: GitHubAutomationEvent,
        target_state_id: uuid.UUID | None,
    ) -> list[GitHubStatusAutomationView]:
        if (
            target_state_id is not None
            and await self._workflow_state_repo.get_by_id(workspace_id, target_state_id) is None
        ):
            raise WorkflowStateNotFoundError()
        await self._automation_repo.upsert(workspace_id, event, target_state_id)
        return await self.list_automations(workspace_id)

    async def _ensure_default_automations(self, workspace_id: uuid.UUID) -> None:
        """Só na primeira conexão: quem reconecta mantém as regras que já editou."""
        if await self._automation_repo.list_by_workspace(workspace_id):
            return
        states = await self._workflow_state_repo.list_by_workspace(workspace_id)
        for event, target_state_id in default_automation_targets(states).items():
            await self._automation_repo.upsert(workspace_id, event, target_state_id)

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
        link_repo: GitHubPullRequestLinkRepositoryProtocol,
        issue_repo: IssueRepositoryProtocol,
        automation_repo: GitHubStatusAutomationRepositoryProtocol,
        sender_repo: GitHubSenderRepositoryProtocol,
        issue_service: IssueService,
    ) -> None:
        """`issue_service` aplica a mudança de status das regras: a regra de negócio
        de transição (guarda de status terminal, atividade, notificação, versão) é de
        Issues, e o webhook só decide quando e para onde."""
        self._installation_repo = installation_repo
        self._delivery_repo = delivery_repo
        self._link_repo = link_repo
        self._issue_repo = issue_repo
        self._automation_repo = automation_repo
        self._sender_repo = sender_repo
        self._issue_service = issue_service

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
        if isinstance(payload, GitHubPullRequestEventPayload):
            if payload.action not in _PULL_REQUEST_ACTIONS:
                return GitHubWebhookOutcome.IGNORED, _REASON_UNHANDLED_ACTION, workspace_id
            return await self._sync_pull_request_links(installation, payload)
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

    async def _sync_pull_request_links(
        self, installation: GitHubInstallation, payload: GitHubPullRequestEventPayload
    ) -> tuple[GitHubWebhookOutcome, str | None, uuid.UUID | None]:
        """Deixa os vínculos deste PR iguais às issues que ele cita agora (ADR-070):
        cria os novos, atualiza o estado dos que continuam e remove os de issues que
        deixaram de ser citadas (ou foram excluídas). Só no workspace da instalação —
        o mesmo `FD-12` de outro workspace nunca é considerado."""
        workspace_id = installation.workspace_id
        pull_request = payload.pull_request
        existing = await self._link_repo.list_by_pull_request(workspace_id, pull_request.id)
        if any(link.pr_updated_at > pull_request.updated_at for link in existing):
            # Entregas chegam fora de ordem; aplicar esta desfaria um estado mais novo.
            return GitHubWebhookOutcome.IGNORED, _REASON_STALE_EVENT, workspace_id

        numbers = extract_issue_numbers(
            [pull_request.head.ref, pull_request.title, pull_request.body]
        )
        issues = await self._issue_repo.list_active_by_numbers(workspace_id, numbers)
        if not issues and not existing:
            return GitHubWebhookOutcome.IGNORED, _REASON_NO_ISSUE_REFERENCE, workspace_id

        links_by_issue = {link.issue_id: link for link in existing}
        newly_linked = [issue for issue in issues if issue.id not in links_by_issue]
        cited_issue_ids = {issue.id for issue in issues}
        await self._link_repo.delete(
            workspace_id, [link.id for link in existing if link.issue_id not in cited_issue_ids]
        )
        for issue in issues:
            link = links_by_issue.get(issue.id)
            if link is None:
                await self._link_repo.create(
                    _apply_pull_request(
                        GitHubPullRequestLink(
                            workspace_id=workspace_id,
                            issue_id=issue.id,
                            pull_request_id=pull_request.id,
                        ),
                        installation,
                        payload,
                    )
                )
            else:
                await self._link_repo.update(_apply_pull_request(link, installation, payload))

        automation_targets = issues if payload.action in _STATE_CHANGE_ACTIONS else newly_linked
        await self._apply_status_automation(workspace_id, payload, automation_targets)
        return GitHubWebhookOutcome.PROCESSED, None, workspace_id

    async def _apply_status_automation(
        self,
        workspace_id: uuid.UUID,
        payload: GitHubPullRequestEventPayload,
        issues: Sequence[Issue],
    ) -> None:
        if not issues:
            return
        event = _AUTOMATION_EVENT_BY_STATE[payload.pull_request.flowdesk_state]
        rule = await self._automation_repo.get(workspace_id, event)
        if rule is None or rule.target_state_id is None:
            return
        actor = await self._resolve_actor(workspace_id, payload.sender)
        moved = 0
        for issue in issues:
            if await self._issue_service.apply_automation_transition(
                workspace_id, issue.id, rule.target_state_id, actor
            ):
                moved += 1
        logger.info(
            "github_automation_applied",
            workspace_id=str(workspace_id),
            automation_event=event.value,
            pull_request_id=payload.pull_request.id,
            issues_moved=moved,
            actor_user_id=str(actor.user_id) if actor.user_id else None,
        )

    async def _resolve_actor(
        self, workspace_id: uuid.UUID, sender: GitHubSenderRef | None
    ) -> AutomationActor:
        member = (
            await self._sender_repo.find_workspace_member(workspace_id, sender.id)
            if sender is not None
            else None
        )
        if member is None:
            return AutomationActor(
                source=ActivityActorSource.GITHUB, user_id=None, name=_GITHUB_ACTOR_NAME
            )
        return AutomationActor(
            source=ActivityActorSource.GITHUB,
            user_id=member.user_id,
            name=f"{member.name} via {_GITHUB_ACTOR_NAME}",
        )


class GitHubPullRequestLinkService:
    def __init__(
        self,
        link_repo: GitHubPullRequestLinkRepositoryProtocol,
        issue_repo: IssueRepositoryProtocol,
    ) -> None:
        self._link_repo = link_repo
        self._issue_repo = issue_repo

    async def list_for_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> Sequence[GitHubPullRequestLink]:
        if await self._issue_repo.get_by_id(workspace_id, issue_id) is None:
            raise IssueNotFoundError()
        return await self._link_repo.list_by_issue(workspace_id, issue_id)


def default_automation_targets(
    states: Sequence[WorkflowState],
) -> dict[GitHubAutomationEvent, uuid.UUID | None]:
    """Defaults gravados na primeira conexão (ADR-070), pela posição no board: o
    primeiro status `STARTED` para rascunho ("In Progress" no seed), o último
    `STARTED` para PR aberto ("In Review"), o primeiro `COMPLETED` para merge. PR
    fechado sem merge não move nada. A categoria sozinha não basta: "In Progress" e
    "In Review" são os dois `STARTED`."""
    ordered = sorted(states, key=lambda state: state.position)
    started = [state.id for state in ordered if state.category == WorkflowStateCategory.STARTED]
    completed = [state.id for state in ordered if state.category == WorkflowStateCategory.COMPLETED]
    return {
        GitHubAutomationEvent.PR_DRAFT: started[0] if started else None,
        GitHubAutomationEvent.PR_OPEN: started[-1] if started else None,
        GitHubAutomationEvent.PR_MERGED: completed[0] if completed else None,
        GitHubAutomationEvent.PR_CLOSED: None,
    }


def _apply_pull_request(
    link: GitHubPullRequestLink,
    installation: GitHubInstallation,
    payload: GitHubPullRequestEventPayload,
) -> GitHubPullRequestLink:
    pull_request = payload.pull_request
    link.installation_id = installation.installation_id
    link.repository_full_name = payload.repository.full_name
    link.pr_number = pull_request.number
    link.pr_url = pull_request.html_url
    link.pr_title = pull_request.title
    link.pr_state = pull_request.flowdesk_state
    link.author_login = pull_request.user.login
    link.head_branch = pull_request.head.ref
    link.pr_updated_at = pull_request.updated_at
    return link


def _parse_installation_id(raw: str | None) -> int | None:
    """O valor chega da query string da navegação de volta do GitHub, então é
    texto livre até prova em contrário."""
    if not raw or not raw.isascii() or not raw.isdigit() or len(raw) > _MAX_INSTALLATION_ID_DIGITS:
        return None
    return int(raw)
