import secrets
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.models import User
from src.features.github.models import GitHubPullRequestLink, GitHubPullRequestState
from src.features.github.repository import GitHubPullRequestLinkRepository
from src.features.issues.models import Issue
from src.features.issues.repository import IssueRepository
from src.features.workspaces.models import Workspace
from src.features.workspaces.repository import WorkspaceRepository
from tests.integration.conftest import unique_suffix


@pytest.fixture
def link_repo(db_session: AsyncSession) -> GitHubPullRequestLinkRepository:
    return GitHubPullRequestLinkRepository(db_session)


@pytest.fixture
async def other_workspace(workspace_repo: WorkspaceRepository, user: User) -> Workspace:
    return await workspace_repo.create(
        Workspace(name="Outra", slug=f"outra-{unique_suffix()}", owner_id=user.id)
    )


def _link(
    issue: Issue, pull_request_id: int, *, updated_at: datetime | None = None
) -> GitHubPullRequestLink:
    return GitHubPullRequestLink(
        workspace_id=issue.workspace_id,
        issue_id=issue.id,
        installation_id=secrets.randbelow(10**9),
        pull_request_id=pull_request_id,
        repository_full_name="acme/api",
        pr_number=7,
        pr_url="https://github.com/acme/api/pull/7",
        pr_title="FD-1",
        pr_state=GitHubPullRequestState.OPEN,
        author_login="ada",
        head_branch="fd-1-login",
        pr_updated_at=updated_at or datetime.now(UTC),
    )


async def test_issue_is_linked_to_a_pull_request_at_most_once(
    db_session: AsyncSession, link_repo: GitHubPullRequestLinkRepository, issue: Issue
) -> None:
    await link_repo.create(_link(issue, 1001))
    db_session.add(_link(issue, 1001))

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_reads_and_deletes_are_scoped_to_the_workspace(
    link_repo: GitHubPullRequestLinkRepository, issue: Issue, other_workspace: Workspace
) -> None:
    older = await link_repo.create(
        _link(issue, 2001, updated_at=datetime.now(UTC) - timedelta(days=1))
    )
    newer = await link_repo.create(_link(issue, 2002))

    by_issue = await link_repo.list_by_issue(issue.workspace_id, issue.id)
    by_pull_request = await link_repo.list_by_pull_request(issue.workspace_id, 2001)

    assert [link.id for link in by_issue] == [newer.id, older.id]
    assert [link.id for link in by_pull_request] == [older.id]
    assert await link_repo.list_by_issue(other_workspace.id, issue.id) == []
    assert await link_repo.list_by_pull_request(other_workspace.id, 2001) == []

    await link_repo.delete(other_workspace.id, [older.id])
    assert len(await link_repo.list_by_issue(issue.workspace_id, issue.id)) == 2
    await link_repo.delete(issue.workspace_id, [older.id])
    assert [link.id for link in await link_repo.list_by_issue(issue.workspace_id, issue.id)] == [
        newer.id
    ]


async def test_issues_are_found_by_number_only_when_active_and_in_the_workspace(
    issue_repo: IssueRepository, issue: Issue, other_workspace: Workspace
) -> None:
    found = await issue_repo.list_active_by_numbers(issue.workspace_id, [issue.number, 999999])
    elsewhere = await issue_repo.list_active_by_numbers(other_workspace.id, [issue.number])
    await issue_repo.soft_delete(issue.id)
    after_delete = await issue_repo.list_active_by_numbers(issue.workspace_id, [issue.number])

    assert [i.id for i in found] == [issue.id]
    assert elsewhere == []
    assert after_delete == []
    assert await issue_repo.list_active_by_numbers(issue.workspace_id, []) == []
