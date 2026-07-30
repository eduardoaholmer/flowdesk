import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.features.issues.models import Issue, IssueLabel
from src.features.issues.repository import IssueRepository
from src.features.labels.models import Label
from src.features.workspaces.models import Workspace


async def test_issue_defaults_and_identifier(
    db_session: AsyncSession, issue: Issue, workspace: Workspace
) -> None:
    stmt = select(Issue).where(Issue.id == issue.id)
    loaded = await db_session.scalar(stmt)

    assert loaded is not None
    assert loaded.workspace_id == workspace.id
    assert loaded.project_id is None
    assert loaded.status_id == issue.status_id
    assert loaded.version == 1
    assert loaded.number == 1
    assert loaded.identifier == "FD-1"


async def test_next_number_is_sequential_and_scoped_per_workspace(
    issue_repo: IssueRepository, workspace: Workspace
) -> None:
    first = await issue_repo.next_number(workspace.id)
    second = await issue_repo.next_number(workspace.id)

    assert first == 1
    assert second == 2


async def test_issue_number_unique_per_workspace(
    issue_repo: IssueRepository,
    workspace: Workspace,
    issue: Issue,
) -> None:
    with pytest.raises(IntegrityError):
        await issue_repo.create(
            Issue(
                workspace_id=workspace.id,
                number=issue.number,
                title="Outra issue com o mesmo número",
                creator_id=issue.creator_id,
                status_id=issue.status_id,
            )
        )


async def test_add_and_remove_label_from_issue(
    db_session: AsyncSession, issue_repo: IssueRepository, issue: Issue, label: Label
) -> None:
    await issue_repo.add_label(issue.id, label.id)

    stmt = select(Issue).options(selectinload(Issue.label_links)).where(Issue.id == issue.id)
    loaded = await db_session.scalar(stmt)
    assert loaded is not None
    assert [link.label_id for link in loaded.label_links] == [label.id]

    await issue_repo.remove_label(issue.id, label.id)
    await db_session.flush()
    remaining = await db_session.scalar(
        select(IssueLabel).where(IssueLabel.issue_id == issue.id, IssueLabel.label_id == label.id)
    )
    assert remaining is None


async def test_issue_label_cascades_when_issue_hard_deleted(
    db_session: AsyncSession, issue_repo: IssueRepository, issue: Issue, label: Label
) -> None:
    """`ON DELETE CASCADE` só é exercitado em delete físico — issues normalmente são
    soft-deleted pela aplicação, mas a constraint precisa se provar correta mesmo
    assim (defesa em profundidade contra um hard delete acidental/administrativo).
    """
    await issue_repo.add_label(issue.id, label.id)
    await db_session.flush()

    await db_session.delete(issue)
    await db_session.flush()

    remaining = await db_session.scalar(select(IssueLabel).where(IssueLabel.issue_id == issue.id))
    assert remaining is None


async def test_sub_issue_persists_parent_id(
    db_session: AsyncSession, issue_repo: IssueRepository, workspace: Workspace, issue: Issue
) -> None:
    child = await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            number=await issue_repo.next_number(workspace.id),
            title="Sub-tarefa",
            creator_id=issue.creator_id,
            status_id=issue.status_id,
            parent_id=issue.id,
        )
    )

    loaded = await db_session.scalar(select(Issue).where(Issue.id == child.id))
    assert loaded is not None
    assert loaded.parent_id == issue.id


async def test_count_children_only_counts_active_non_deleted_children(
    issue_repo: IssueRepository, workspace: Workspace, issue: Issue
) -> None:
    child = await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            number=await issue_repo.next_number(workspace.id),
            title="Filho",
            creator_id=issue.creator_id,
            status_id=issue.status_id,
            parent_id=issue.id,
        )
    )

    assert await issue_repo.count_children(workspace.id, issue.id) == 1

    await issue_repo.soft_delete(child.id)

    assert await issue_repo.count_children(workspace.id, issue.id) == 0


async def test_list_by_workspace_filters_by_parent_id(
    issue_repo: IssueRepository, workspace: Workspace, issue: Issue
) -> None:
    child = await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            number=await issue_repo.next_number(workspace.id),
            title="Filho",
            creator_id=issue.creator_id,
            status_id=issue.status_id,
            parent_id=issue.id,
        )
    )
    await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            number=await issue_repo.next_number(workspace.id),
            title="Solta",
            creator_id=issue.creator_id,
            status_id=issue.status_id,
        )
    )

    children = await issue_repo.list_by_workspace(workspace.id, parent_id=issue.id)

    assert [i.id for i in children] == [child.id]


async def test_hard_deleting_a_parent_with_children_is_restricted(
    db_session: AsyncSession, issue_repo: IssueRepository, workspace: Workspace, issue: Issue
) -> None:
    """`ON DELETE RESTRICT` — mesma defesa em profundidade da constraint de
    label acima, para o caso de um hard delete acidental atingir um pai com
    filhos vinculados (a aplicação em si nunca hard-deleta, sempre soft delete
    via `IssueService.delete`, que já bloqueia esse caso em nível de serviço)."""
    await issue_repo.create(
        Issue(
            workspace_id=workspace.id,
            number=await issue_repo.next_number(workspace.id),
            title="Filho",
            creator_id=issue.creator_id,
            status_id=issue.status_id,
            parent_id=issue.id,
        )
    )
    await db_session.flush()

    await db_session.delete(issue)
    with pytest.raises(IntegrityError):
        await db_session.flush()
