from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.features.auth.models import User
from src.features.comments.models import Comment, CommentMention
from src.features.comments.repository import CommentRepository
from src.features.issues.models import ActivityLog, Issue
from src.features.issues.repository import IssueRepository


async def test_comment_linked_to_issue(
    db_session: AsyncSession, issue: Issue, comment: Comment
) -> None:
    stmt = select(Issue).options(selectinload(Issue.comments)).where(Issue.id == issue.id)
    loaded = await db_session.scalar(stmt)

    assert loaded is not None
    assert len(loaded.comments) == 1
    assert loaded.comments[0].body == "oi"


async def test_activity_log_is_append_only_and_ordered(
    db_session: AsyncSession, issue_repo: IssueRepository, issue: Issue
) -> None:
    assert not hasattr(ActivityLog, "updated_at")
    assert not hasattr(ActivityLog, "deleted_at")

    await issue_repo.record_activity(
        ActivityLog(
            workspace_id=issue.workspace_id,
            issue_id=issue.id,
            actor_id=issue.creator_id,
            action="created",
        )
    )
    await issue_repo.record_activity(
        ActivityLog(
            workspace_id=issue.workspace_id,
            issue_id=issue.id,
            actor_id=issue.creator_id,
            action="status_changed",
            field="status_id",
            old_value="todo",
            new_value="in_progress",
        )
    )

    stmt = (
        select(ActivityLog).where(ActivityLog.issue_id == issue.id).order_by(ActivityLog.created_at)
    )
    entries = (await db_session.scalars(stmt)).all()
    assert [entry.action for entry in entries] == ["created", "status_changed"]


async def test_comment_repository_pagination_and_soft_delete(
    comment_repo: CommentRepository, issue: Issue, user: User
) -> None:
    for i in range(3):
        await comment_repo.create(
            Comment(
                workspace_id=issue.workspace_id, issue_id=issue.id, author_id=user.id, body=f"c{i}"
            )
        )

    first_page = await comment_repo.list_by_issue(issue.id, page=1, per_page=2)
    total = await comment_repo.count_by_issue(issue.id)
    assert len(first_page) == 2
    assert total == 3

    await comment_repo.soft_delete(first_page[0].id)
    remaining_total = await comment_repo.count_by_issue(issue.id)
    assert remaining_total == 2


async def test_comment_mentions_cascade_when_comment_hard_deleted(
    db_session: AsyncSession, comment_repo: CommentRepository, comment: Comment, user: User
) -> None:
    """`comment_mentions.comment_id` usa `ON DELETE CASCADE` (mesmo padrão de
    `issue_labels`) — a relação existe ou não, sem estado "excluído logicamente"
    próprio (`docs/03-database.md` §2).
    """
    await comment_repo.add_mentions(comment.id, [user.id])
    await db_session.flush()

    await db_session.delete(comment)
    await db_session.flush()

    remaining = await db_session.scalar(
        select(CommentMention).where(CommentMention.comment_id == comment.id)
    )
    assert remaining is None
