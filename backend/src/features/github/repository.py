import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.github.models import GitHubInstallation

_CONNECT_STATE_KEY_PREFIX = "github:connect:"


@dataclass(frozen=True)
class GitHubConnectIntent:
    """Quem pediu para conectar e para qual workspace — gravado no servidor no
    `connect` e recuperado no retorno do GitHub pelo `state`, para que o callback
    nunca dependa de um `workspace_id` vindo da URL."""

    workspace_id: uuid.UUID
    user_id: uuid.UUID


class GitHubInstallationRepositoryProtocol(Protocol):
    async def create(self, installation: GitHubInstallation) -> GitHubInstallation: ...
    async def get_by_id(
        self, workspace_id: uuid.UUID, installation_pk: uuid.UUID
    ) -> GitHubInstallation | None: ...
    async def get_active_by_installation_id(
        self, installation_id: int
    ) -> GitHubInstallation | None: ...
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[GitHubInstallation]: ...
    async def update(self, installation: GitHubInstallation) -> GitHubInstallation: ...
    async def soft_delete(self, workspace_id: uuid.UUID, installation_pk: uuid.UUID) -> None: ...


class GitHubConnectStateRepositoryProtocol(Protocol):
    async def save(self, state: str, intent: GitHubConnectIntent, ttl_seconds: int) -> None: ...
    async def pop(self, state: str) -> GitHubConnectIntent | None: ...


class GitHubInstallationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, installation: GitHubInstallation) -> GitHubInstallation:
        self._session.add(installation)
        await self._session.flush()
        return installation

    async def get_by_id(
        self, workspace_id: uuid.UUID, installation_pk: uuid.UUID
    ) -> GitHubInstallation | None:
        stmt = select(GitHubInstallation).where(
            GitHubInstallation.id == installation_pk,
            GitHubInstallation.workspace_id == workspace_id,
            GitHubInstallation.deleted_at.is_(None),
        )
        result: GitHubInstallation | None = await self._session.scalar(stmt)
        return result

    async def get_active_by_installation_id(
        self, installation_id: int
    ) -> GitHubInstallation | None:
        """Sem `workspace_id` de propósito: a instalação é única entre todos os
        workspaces (`uq_github_installations_installation_id_active`), e a pergunta
        aqui é justamente "ela já pertence a algum workspace?". O service só usa o
        resultado para decidir entre reconexão e conflito, nunca o devolve a quem
        não é do workspace dono."""
        stmt = select(GitHubInstallation).where(
            GitHubInstallation.installation_id == installation_id,
            GitHubInstallation.deleted_at.is_(None),
        )
        result: GitHubInstallation | None = await self._session.scalar(stmt)
        return result

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[GitHubInstallation]:
        stmt = (
            select(GitHubInstallation)
            .where(
                GitHubInstallation.workspace_id == workspace_id,
                GitHubInstallation.deleted_at.is_(None),
            )
            .order_by(GitHubInstallation.created_at.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def update(self, installation: GitHubInstallation) -> GitHubInstallation:
        await self._session.flush()
        return installation

    async def soft_delete(self, workspace_id: uuid.UUID, installation_pk: uuid.UUID) -> None:
        await self._session.execute(
            update(GitHubInstallation)
            .where(
                GitHubInstallation.id == installation_pk,
                GitHubInstallation.workspace_id == workspace_id,
            )
            .values(deleted_at=datetime.now(UTC))
        )


class GitHubConnectStateRepository:
    """`state` da conexão em Redis, de uso único (`GETDEL`) e com expiração. A chave
    é o hash do `state`, mesmo cuidado dos tokens guardados no banco: quem lê o
    Redis não consegue montar uma URL de retorno válida."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def save(self, state: str, intent: GitHubConnectIntent, ttl_seconds: int) -> None:
        value = json.dumps(
            {"workspace_id": str(intent.workspace_id), "user_id": str(intent.user_id)}
        )
        await self._redis.set(_state_key(state), value, ex=ttl_seconds)

    async def pop(self, state: str) -> GitHubConnectIntent | None:
        value = await self._redis.getdel(_state_key(state))
        if value is None:
            return None
        payload = json.loads(value)
        return GitHubConnectIntent(
            workspace_id=uuid.UUID(payload["workspace_id"]),
            user_id=uuid.UUID(payload["user_id"]),
        )


def _state_key(state: str) -> str:
    return _CONNECT_STATE_KEY_PREFIX + hashlib.sha256(state.encode("utf-8")).hexdigest()
