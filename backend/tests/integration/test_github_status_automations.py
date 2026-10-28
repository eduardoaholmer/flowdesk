import secrets
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.models import OAuthIdentity, User
from src.features.github.models import GitHubAutomationEvent
from src.features.github.repository import (
    GitHubSenderRepository,
    GitHubStatusAutomationRepository,
)
from src.features.issues.models import ActivityActorSource, ActivityLog, Issue
from src.features.workflow_states.models import WorkflowState, WorkflowStateCategory
from src.features.workflow_states.repository import WorkflowStateRepository
from src.features.workspaces.models import Workspace
from src.features.workspaces.repository import WorkspaceRepository


@pytest.fixture
def automation_repo(db_session: AsyncSession) -> GitHubStatusAutomationRepository:
    return GitHubStatusAutomationRepository(db_session)


@pytest.fixture
def sender_repo(db_session: AsyncSession) -> GitHubSenderRepository:
    return GitHubSenderRepository(db_session)


async def _github_identity(db_session: AsyncSession, user: User) -> int:
    github_user_id = secrets.randbelow(10**9) + 1
    db_session.add(
        OAuthIdentity(user_id=user.id, provider="github", provider_user_id=str(github_user_id))
    )
    await db_session.flush()
    return github_user_id


async def test_activity_by_a_person_requires_an_author(
    db_session: AsyncSession, issue: Issue
) -> None:
    db_session.add(
        ActivityLog(
            workspace_id=issue.workspace_id,
            issue_id=issue.id,
            actor_id=None,
            actor_source=ActivityActorSource.USER,
            action="issue.status_changed",
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_automation_activity_may_have_no_author(
    db_session: AsyncSession, issue: Issue
) -> None:
    entry = ActivityLog(
        workspace_id=issue.workspace_id,
        issue_id=issue.id,
        actor_id=None,
        actor_source=ActivityActorSource.GITHUB,
        action="issue.status_changed",
    )
    db_session.add(entry)
    await db_session.flush()

    assert entry.id is not None


async def test_existing_style_activity_defaults_to_user(
    db_session: AsyncSession, issue: Issue, user: User
) -> None:
    entry = ActivityLog(
        workspace_id=issue.workspace_id,
        issue_id=issue.id,
        actor_id=user.id,
        action="issue.updated",
    )
    db_session.add(entry)
    await db_session.flush()

    assert entry.actor_source == ActivityActorSource.USER


async def test_upsert_creates_then_updates_one_rule_per_event(
    automation_repo: GitHubStatusAutomationRepository,
    workspace: Workspace,
    workflow_state: WorkflowState,
) -> None:
    await automation_repo.upsert(workspace.id, GitHubAutomationEvent.PR_MERGED, None)
    before = await automation_repo.get(workspace.id, GitHubAutomationEvent.PR_MERGED)
    assert before is not None
    assert before.target_state_id is None

    await automation_repo.upsert(workspace.id, GitHubAutomationEvent.PR_MERGED, workflow_state.id)

    after = await automation_repo.get(workspace.id, GitHubAutomationEvent.PR_MERGED)
    rules = await automation_repo.list_by_workspace(workspace.id)
    assert after is not None
    assert after.target_state_id == workflow_state.id
    assert len(rules) == 1


async def test_deleting_a_status_repoints_rules_that_targeted_it(
    db_session: AsyncSession,
    automation_repo: GitHubStatusAutomationRepository,
    workflow_state_repo: WorkflowStateRepository,
    workspace: Workspace,
    workflow_state: WorkflowState,
) -> None:
    other = await workflow_state_repo.create(
        WorkflowState(
            workspace_id=workspace.id,
            name="Shipped",
            category=WorkflowStateCategory.COMPLETED,
            position=99,
            is_default=False,
        )
    )
    await automation_repo.upsert(workspace.id, GitHubAutomationEvent.PR_MERGED, workflow_state.id)
    await automation_repo.upsert(workspace.id, GitHubAutomationEvent.PR_OPEN, other.id)

    await workflow_state_repo.repoint_github_automations(workflow_state.id, None)

    merged = await automation_repo.get(workspace.id, GitHubAutomationEvent.PR_MERGED)
    opened = await automation_repo.get(workspace.id, GitHubAutomationEvent.PR_OPEN)
    assert merged is not None and merged.target_state_id is None
    assert opened is not None and opened.target_state_id == other.id


async def test_sender_is_found_only_as_an_active_member_with_that_github_account(
    db_session: AsyncSession,
    sender_repo: GitHubSenderRepository,
    workspace: Workspace,
    user: User,
) -> None:
    github_user_id = await _github_identity(db_session, user)

    found = await sender_repo.find_workspace_member(workspace.id, github_user_id)
    unknown_account = await sender_repo.find_workspace_member(workspace.id, github_user_id + 1)

    assert found is not None
    assert (found.user_id, found.name) == (user.id, user.name)
    assert unknown_account is None


async def test_sender_who_left_the_workspace_is_not_the_author(
    db_session: AsyncSession,
    sender_repo: GitHubSenderRepository,
    workspace_repo: WorkspaceRepository,
    workspace: Workspace,
    user: User,
) -> None:
    github_user_id = await _github_identity(db_session, user)
    member = await workspace_repo.get_member(workspace.id, user.id)
    assert member is not None
    member.deleted_at = datetime.now(UTC)
    await db_session.flush()

    assert await sender_repo.find_workspace_member(workspace.id, github_user_id) is None
