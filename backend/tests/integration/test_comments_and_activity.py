from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.features.comments.models import Comment
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
