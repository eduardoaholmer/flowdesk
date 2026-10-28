import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.core.authorization import PermissionService
from src.features.github.client import GitHubInstallationInfo
from src.features.github.models import (
    GitHubAutomationEvent,
    GitHubInstallation,
    GitHubPullRequestLink,
    GitHubStatusAutomation,
    GitHubWebhookDelivery,
    GitHubWebhookOutcome,
)
from src.features.github.repository import GitHubConnectIntent, GitHubSenderMember
from src.features.issues.service import IssueService
from src.features.notifications.service import NotificationService
from uuid6 import uuid7

from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.labels.fakes import FakeLabelRepository
from tests.unit.features.notifications.fakes import FakeNotificationRepository
from tests.unit.features.projects.fakes import FakeProjectRepository
from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository
from tests.unit.features.workspaces.fakes import FakeWorkspaceRepository


class FakeGitHubInstallationRepository:
    """Implementa `GitHubInstallationRepositoryProtocol` em memória — mesmo
    racional de `tests/unit/features/workflow_states/fakes.py`."""

    def __init__(self) -> None:
        self.installations: dict[uuid.UUID, GitHubInstallation] = {}

    async def create(self, installation: GitHubInstallation) -> GitHubInstallation:
        if installation.id is None:
            installation.id = uuid7()
        now = datetime.now(UTC)
        installation.created_at = installation.created_at or now
        installation.updated_at = installation.updated_at or now
        self.installations[installation.id] = installation
        return installation

    async def get_by_id(
        self, workspace_id: uuid.UUID, installation_pk: uuid.UUID
    ) -> GitHubInstallation | None:
        installation = self.installations.get(installation_pk)
        if (
            installation is None
            or installation.workspace_id != workspace_id
            or installation.deleted_at is not None
        ):
            return None
        return installation

    async def get_active_by_installation_id(
        self, installation_id: int
    ) -> GitHubInstallation | None:
        for installation in self.installations.values():
            if installation.installation_id == installation_id and installation.deleted_at is None:
                return installation
        return None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[GitHubInstallation]:
        return [
            installation
            for installation in self.installations.values()
            if installation.workspace_id == workspace_id and installation.deleted_at is None
        ]

    async def update(self, installation: GitHubInstallation) -> GitHubInstallation:
        installation.updated_at = datetime.now(UTC)
        return installation

    async def soft_delete(self, workspace_id: uuid.UUID, installation_pk: uuid.UUID) -> None:
        installation = self.installations.get(installation_pk)
        if installation is not None and installation.workspace_id == workspace_id:
            installation.deleted_at = datetime.now(UTC)


class FakeGitHubConnectStateRepository:
    def __init__(self) -> None:
        self.states: dict[str, GitHubConnectIntent] = {}
        self.ttls: dict[str, int] = {}

    async def save(self, state: str, intent: GitHubConnectIntent, ttl_seconds: int) -> None:
        self.states[state] = intent
        self.ttls[state] = ttl_seconds

    async def pop(self, state: str) -> GitHubConnectIntent | None:
        return self.states.pop(state, None)


class FakeGitHubAppClient:
    """`installations` simula o que `GET /user/installations` devolveria para o
    usuário que autorizou; `codes` registra cada troca, para os testes conferirem
    que o GitHub nem foi consultado quando a checagem local já recusa."""

    def __init__(self, installations: Sequence[GitHubInstallationInfo] = ()) -> None:
        self.installations = list(installations)
        self.codes: list[str] = []

    def installation_url(self, state: str) -> str:
        return f"https://github.com/apps/flowdesk-test/installations/new?state={state}"

    async def find_user_installation(
        self, code: str, installation_id: int
    ) -> GitHubInstallationInfo | None:
        self.codes.append(code)
        for info in self.installations:
            if info.installation_id == installation_id:
                return info
        return None


class FakeGitHubWebhookDeliveryRepository:
    def __init__(self) -> None:
        self.deliveries: dict[str, GitHubWebhookDelivery] = {}

    async def claim(
        self,
        *,
        delivery_id: str,
        event: str,
        action: str | None,
        installation_id: int | None,
    ) -> bool:
        if delivery_id in self.deliveries:
            return False
        self.deliveries[delivery_id] = GitHubWebhookDelivery(
            delivery_id=delivery_id,
            event=event,
            action=action,
            installation_id=installation_id,
            outcome=GitHubWebhookOutcome.PROCESSED,
            received_at=datetime.now(UTC),
        )
        return True

    async def get(self, delivery_id: str) -> GitHubWebhookDelivery | None:
        return self.deliveries.get(delivery_id)

    async def finish(
        self,
        delivery_id: str,
        *,
        outcome: GitHubWebhookOutcome,
        reason: str | None,
        workspace_id: uuid.UUID | None,
    ) -> None:
        delivery = self.deliveries[delivery_id]
        delivery.outcome = outcome
        delivery.reason = reason
        delivery.workspace_id = workspace_id


class FakeGitHubPullRequestLinkRepository:
    def __init__(self) -> None:
        self.links: dict[uuid.UUID, GitHubPullRequestLink] = {}

    async def list_by_pull_request(
        self, workspace_id: uuid.UUID, pull_request_id: int
    ) -> Sequence[GitHubPullRequestLink]:
        return [
            link
            for link in self.links.values()
            if link.workspace_id == workspace_id and link.pull_request_id == pull_request_id
        ]

    async def list_by_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> Sequence[GitHubPullRequestLink]:
        links = [
            link
            for link in self.links.values()
            if link.workspace_id == workspace_id and link.issue_id == issue_id
        ]
        return sorted(links, key=lambda link: link.pr_updated_at, reverse=True)

    async def create(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink:
        if link.id is None:
            link.id = uuid7()
        now = datetime.now(UTC)
        link.created_at = link.created_at or now
        link.updated_at = link.updated_at or now
        self.links[link.id] = link
        return link

    async def update(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink:
        link.updated_at = datetime.now(UTC)
        return link

    async def delete(self, workspace_id: uuid.UUID, link_ids: Sequence[uuid.UUID]) -> None:
        for link_id in link_ids:
            link = self.links.get(link_id)
            if link is not None and link.workspace_id == workspace_id:
                del self.links[link_id]


class FakeGitHubStatusAutomationRepository:
    def __init__(self) -> None:
        self.rules: dict[tuple[uuid.UUID, GitHubAutomationEvent], GitHubStatusAutomation] = {}

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[GitHubStatusAutomation]:
        return [rule for (ws, _), rule in self.rules.items() if ws == workspace_id]

    async def get(
        self, workspace_id: uuid.UUID, event: GitHubAutomationEvent
    ) -> GitHubStatusAutomation | None:
        return self.rules.get((workspace_id, event))

    async def upsert(
        self,
        workspace_id: uuid.UUID,
        event: GitHubAutomationEvent,
        target_state_id: uuid.UUID | None,
    ) -> None:
        rule = self.rules.get((workspace_id, event))
        if rule is None:
            self.rules[(workspace_id, event)] = GitHubStatusAutomation(
                id=uuid7(), workspace_id=workspace_id, event=event, target_state_id=target_state_id
            )
        else:
            rule.target_state_id = target_state_id


class FakeGitHubSenderRepository:
    """`members` mapeia (workspace, id da conta do GitHub) → membro, simulando o
    join `OAuthIdentity` × `WorkspaceMember` × `User` do repository real."""

    def __init__(self) -> None:
        self.members: dict[tuple[uuid.UUID, int], GitHubSenderMember] = {}

    async def find_workspace_member(
        self, workspace_id: uuid.UUID, github_user_id: int
    ) -> GitHubSenderMember | None:
        return self.members.get((workspace_id, github_user_id))


def make_issue_service(
    issue_repo: FakeIssueRepository,
    workflow_state_repo: FakeWorkflowStateRepository,
    notification_repo: FakeNotificationRepository | None = None,
) -> IssueService:
    """`IssueService` real sobre fakes — o webhook delega a ele a transição de
    status, e o teste precisa da regra de negócio de verdade (guarda de status
    terminal, atividade, notificação), não de um dublê."""
    return IssueService(
        issue_repo,
        PermissionService(),
        FakeProjectRepository(),
        FakeLabelRepository(),
        NotificationService(notification_repo or FakeNotificationRepository()),
        workflow_state_repo,
        FakeWorkspaceRepository(),
    )
