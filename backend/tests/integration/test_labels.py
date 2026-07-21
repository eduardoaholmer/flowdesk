import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.issues.models import Issue
from src.features.issues.repository import IssueRepository
from src.features.labels.models import Label
from src.features.labels.repository import LabelRepository
from src.features.workspaces.models import Workspace


async def test_label_name_unique_per_workspace_while_active(
    label_repo: LabelRepository, workspace: Workspace, label: Label
) -> None:
    with pytest.raises(IntegrityError):
        await label_repo.create(Label(workspace_id=workspace.id, name=label.name, color="#00FF00"))


async def test_label_name_free_again_after_soft_delete(
    db_session: AsyncSession, label_repo: LabelRepository, workspace: Workspace, label: Label
) -> None:
    await label_repo.soft_delete(label.id)
    await db_session.flush()

    recreated = await label_repo.create(
        Label(workspace_id=workspace.id, name=label.name, color="#00FF00")
    )

    assert recreated.id != label.id
    assert await label_repo.get_by_id(workspace.id, label.id) is None


async def test_list_by_workspace_excludes_soft_deleted(
    db_session: AsyncSession, label_repo: LabelRepository, workspace: Workspace, label: Label
) -> None:
    other = await label_repo.create(
        Label(workspace_id=workspace.id, name="feature", color="#00FF00")
    )
    await label_repo.soft_delete(other.id)
    await db_session.flush()

    labels = await label_repo.list_by_workspace(workspace.id)

    assert [item.id for item in labels] == [label.id]


async def test_issue_counts_counts_only_non_deleted_issues(
    db_session: AsyncSession,
    label_repo: LabelRepository,
    issue_repo: IssueRepository,
    workspace: Workspace,
    label: Label,
    issue: Issue,
) -> None:
    await issue_repo.add_label(issue.id, label.id)
    number = await issue_repo.next_number(workspace.id)
    deleted_issue = await issue_repo.create(
        Issue(workspace_id=workspace.id, number=number, title="t", creator_id=issue.creator_id)
    )
    await issue_repo.add_label(deleted_issue.id, label.id)
    await issue_repo.soft_delete(deleted_issue.id)
    await db_session.flush()

    counts = await label_repo.issue_counts([label.id])

    assert counts[label.id] == 1
