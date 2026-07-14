from datetime import UTC, datetime, timedelta

from src.core.security import hash_refresh_token
from src.features.auth.models import RefreshToken, Session, User
from src.features.auth.repository import SessionRepository


async def test_revoke_refresh_token_marks_revoked_and_links_replacement(
    session_repo: SessionRepository, user: User
) -> None:
    session = await session_repo.create_session(Session(user_id=user.id))
    old_token = await session_repo.create_refresh_token(
        RefreshToken(
            session_id=session.id,
            token_hash=hash_refresh_token("old-token"),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    new_token = await session_repo.create_refresh_token(
        RefreshToken(
            session_id=session.id,
            token_hash=hash_refresh_token("new-token"),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )

    await session_repo.revoke_refresh_token(old_token.id, replaced_by_id=new_token.id)

    refreshed = await session_repo.get_refresh_token_by_hash(hash_refresh_token("old-token"))

    assert refreshed is not None
    assert refreshed.revoked_at is not None
    assert refreshed.replaced_by_id == new_token.id


async def test_revoke_refresh_token_does_not_touch_unrelated_token(
    session_repo: SessionRepository, user: User
) -> None:
    session = await session_repo.create_session(Session(user_id=user.id))
    target = await session_repo.create_refresh_token(
        RefreshToken(
            session_id=session.id,
            token_hash=hash_refresh_token("target-token"),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    await session_repo.create_refresh_token(
        RefreshToken(
            session_id=session.id,
            token_hash=hash_refresh_token("other-token"),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )

    await session_repo.revoke_refresh_token(target.id)

    other_hash = hash_refresh_token("other-token")
    other_refreshed = await session_repo.get_refresh_token_by_hash(other_hash)

    assert other_refreshed is not None
    assert other_refreshed.revoked_at is None
