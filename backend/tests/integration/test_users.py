from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.models import User
from src.features.auth.repository import UserRepository


async def test_create_and_fetch_user(user_repo: UserRepository, user: User) -> None:
    fetched = await user_repo.get_by_id(user.id)

    assert fetched is not None
    assert fetched.email == user.email
    assert fetched.deleted_at is None


async def test_get_by_email_is_case_insensitive(user_repo: UserRepository, user: User) -> None:
    fetched = await user_repo.get_by_email(user.email.upper())

    assert fetched is not None
    assert fetched.id == user.id


async def test_soft_deleted_user_not_returned_by_get_by_id(
    db_session: AsyncSession, user_repo: UserRepository, user: User
) -> None:
    user.deleted_at = datetime.now(UTC)
    await db_session.flush()

    assert await user_repo.get_by_id(user.id) is None


async def test_email_unique_case_insensitive(
    db_session: AsyncSession, user_repo: UserRepository, user: User
) -> None:
    duplicate = User(
        name="Another Ada",
        email=user.email.upper(),
        password_hash="not-a-real-hash",
    )

    with pytest.raises(IntegrityError):
        await user_repo.create(duplicate)
