import uuid
from datetime import UTC, datetime

import pytest
from src.features.github.models import (
    GitHubInstallation,
    GitHubPullRequestState,
    GitHubWebhookOutcome,
)
from src.features.github.schemas import GitHubWebhookDeliveryInput
from src.features.github.service import GitHubPullRequestLinkService, GitHubWebhookService
from src.features.issues.exceptions import IssueNotFoundError
from src.features.issues.models import Issue, IssuePriority

from tests.github_payloads import pull_request_payload
from tests.unit.features.github.fakes import (
    FakeGitHubInstallationRepository,
    FakeGitHubPullRequestLinkRepository,
    FakeGitHubSenderRepository,
    FakeGitHubStatusAutomationRepository,
    FakeGitHubWebhookDeliveryRepository,
    make_issue_service,
)
from tests.unit.features.issues.fakes import FakeIssueRepository
from tests.unit.features.workflow_states.fakes import FakeWorkflowStateRepository

_INSTALLATION_ID = 4242


@pytest.fixture
def installation_repo() -> FakeGitHubInstallationRepository:
    return FakeGitHubInstallationRepository()


@pytest.fixture
def delivery_repo() -> FakeGitHubWebhookDeliveryRepository:
    return FakeGitHubWebhookDeliveryRepository()


@pytest.fixture
def link_repo() -> FakeGitHubPullRequestLinkRepository:
    return FakeGitHubPullRequestLinkRepository()


@pytest.fixture
def issue_repo() -> FakeIssueRepository:
    return FakeIssueRepository()


@pytest.fixture
def service(
    installation_repo: FakeGitHubInstallationRepository,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> GitHubWebhookService:
    return GitHubWebhookService(
        installation_repo,
        delivery_repo,
        link_repo,
        issue_repo,
        FakeGitHubStatusAutomationRepository(),
        FakeGitHubSenderRepository(),
        make_issue_service(issue_repo, FakeWorkflowStateRepository()),
    )


@pytest.fixture
async def installation(installation_repo: FakeGitHubInstallationRepository) -> GitHubInstallation:
    return await installation_repo.create(
        GitHubInstallation(
            workspace_id=uuid.uuid4(),
            installation_id=_INSTALLATION_ID,
            account_login="Codertocat",
            account_type="User",
            connected_by_id=uuid.uuid4(),
        )
    )


async def _issue(issue_repo: FakeIssueRepository, workspace_id: uuid.UUID, number: int) -> Issue:
    return await issue_repo.create(
        Issue(
            workspace_id=workspace_id,
            number=number,
            title=f"Issue {number}",
            status_id=uuid.uuid4(),
            priority=IssuePriority.NO_PRIORITY,
            creator_id=uuid.uuid4(),
        )
    )


async def _deliver(
    service: GitHubWebhookService, **overrides: object
) -> tuple[GitHubWebhookOutcome, str]:
    delivery = GitHubWebhookDeliveryInput.parse(
        delivery_id=str(uuid.uuid4()),
        event="pull_request",
        body=pull_request_payload(installation_id=_INSTALLATION_ID, **overrides),  # type: ignore[arg-type]
    )
    result = await service.handle(delivery)
    return result.outcome, delivery.delivery_id


def _linked_numbers(
    link_repo: FakeGitHubPullRequestLinkRepository, issue_repo: FakeIssueRepository
) -> set[int]:
    return {issue_repo.issues[link.issue_id].number for link in link_repo.links.values()}


async def test_pull_request_citing_issues_links_them_with_its_details(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    await _issue(issue_repo, installation.workspace_id, 1)
    await _issue(issue_repo, installation.workspace_id, 2)

    outcome, _ = await _deliver(
        service, branch="fd-1-corrige-login", title="Corrige login", body="Relacionado a FD-2."
    )

    assert outcome == GitHubWebhookOutcome.PROCESSED
    assert _linked_numbers(link_repo, issue_repo) == {1, 2}
    link = next(iter(link_repo.links.values()))
    assert link.workspace_id == installation.workspace_id
    assert link.installation_id == _INSTALLATION_ID
    assert link.pull_request_id == 279147437
    assert link.repository_full_name == "Codertocat/Hello-World"
    assert link.pr_number == 2
    assert link.pr_url == "https://github.com/Codertocat/Hello-World/pull/2"
    assert link.pr_title == "Corrige login"
    assert link.pr_state == GitHubPullRequestState.OPEN
    assert link.author_login == "Codertocat"
    assert link.head_branch == "fd-1-corrige-login"
    assert link.pr_updated_at == datetime(2019, 5, 15, 15, 20, 33, tzinfo=UTC)


async def test_identifier_without_active_issue_is_ignored(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
) -> None:
    deleted = await _issue(issue_repo, installation.workspace_id, 3)
    deleted.deleted_at = datetime.now(UTC)

    outcome, delivery_id = await _deliver(service, title="FD-3 e FD-99")

    assert outcome == GitHubWebhookOutcome.IGNORED
    assert delivery_repo.deliveries[delivery_id].reason == "no_issue_reference"
    assert link_repo.links == {}


async def test_same_number_in_another_workspace_is_never_linked(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    """O prefixo `FD` é igual em todos os workspaces; quem decide o workspace é a
    instalação (ADR-068)."""
    await _issue(issue_repo, uuid.uuid4(), 5)

    outcome, _ = await _deliver(service, title="FD-5")

    assert outcome == GitHubWebhookOutcome.IGNORED
    assert link_repo.links == {}


async def test_editing_the_pull_request_adds_and_removes_links(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    for number in (1, 2, 3):
        await _issue(issue_repo, installation.workspace_id, number)
    await _deliver(service, title="FD-1 e FD-2")
    kept_link_id = next(
        link.id for link in link_repo.links.values() if issue_repo.issues[link.issue_id].number == 1
    )

    outcome, _ = await _deliver(
        service, action="edited", title="FD-1 e FD-3", updated_at="2019-05-15T16:00:00Z"
    )

    assert outcome == GitHubWebhookOutcome.PROCESSED
    assert _linked_numbers(link_repo, issue_repo) == {1, 3}
    assert kept_link_id in link_repo.links
    assert link_repo.links[kept_link_id].pr_title == "FD-1 e FD-3"


async def test_removing_every_reference_removes_every_link(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    await _issue(issue_repo, installation.workspace_id, 1)
    await _deliver(service, title="FD-1")

    outcome, _ = await _deliver(
        service, action="edited", title="Sem referência", updated_at="2019-05-15T16:00:00Z"
    )

    assert outcome == GitHubWebhookOutcome.PROCESSED
    assert link_repo.links == {}


@pytest.mark.parametrize(
    ("overrides", "expected_state"),
    [
        ({"action": "opened", "draft": True}, GitHubPullRequestState.DRAFT),
        ({"action": "converted_to_draft", "draft": True}, GitHubPullRequestState.DRAFT),
        ({"action": "ready_for_review", "draft": False}, GitHubPullRequestState.OPEN),
        ({"action": "closed", "state": "closed", "merged": True}, GitHubPullRequestState.MERGED),
        ({"action": "closed", "state": "closed", "merged": False}, GitHubPullRequestState.CLOSED),
        ({"action": "reopened"}, GitHubPullRequestState.OPEN),
    ],
    ids=["draft", "converted", "ready", "merged", "closed", "reopened"],
)
async def test_link_follows_the_pull_request_state(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
    overrides: dict[str, object],
    expected_state: GitHubPullRequestState,
) -> None:
    await _issue(issue_repo, installation.workspace_id, 1)

    await _deliver(service, title="FD-1", **overrides)

    [link] = link_repo.links.values()
    assert link.pr_state == expected_state


async def test_older_event_does_not_overwrite_a_newer_one(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
    delivery_repo: FakeGitHubWebhookDeliveryRepository,
) -> None:
    """O GitHub não garante ordem de entrega: o `closed` pode chegar antes de um
    `edited` disparado antes dele."""
    await _issue(issue_repo, installation.workspace_id, 1)
    await _deliver(
        service,
        action="closed",
        title="FD-1",
        state="closed",
        merged=True,
        updated_at="2019-05-15T17:00:00Z",
    )

    outcome, delivery_id = await _deliver(
        service, action="edited", title="FD-1 renomeado", updated_at="2019-05-15T16:00:00Z"
    )

    assert outcome == GitHubWebhookOutcome.IGNORED
    assert delivery_repo.deliveries[delivery_id].reason == "stale_event"
    [link] = link_repo.links.values()
    assert link.pr_state == GitHubPullRequestState.MERGED
    assert link.pr_title == "FD-1"


async def test_actions_that_do_not_change_links_are_ignored(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    await _issue(issue_repo, installation.workspace_id, 1)

    outcome, _ = await _deliver(service, action="labeled", title="FD-1")

    assert outcome == GitHubWebhookOutcome.IGNORED
    assert link_repo.links == {}


async def test_listing_links_requires_an_active_issue_of_the_workspace(
    service: GitHubWebhookService,
    installation: GitHubInstallation,
    link_repo: FakeGitHubPullRequestLinkRepository,
    issue_repo: FakeIssueRepository,
) -> None:
    issue = await _issue(issue_repo, installation.workspace_id, 1)
    await _deliver(service, title="FD-1")
    link_service = GitHubPullRequestLinkService(link_repo, issue_repo)

    links = await link_service.list_for_issue(installation.workspace_id, issue.id)

    assert [link.pr_number for link in links] == [2]
    with pytest.raises(IssueNotFoundError):
        await link_service.list_for_issue(uuid.uuid4(), issue.id)
