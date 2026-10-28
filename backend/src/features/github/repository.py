import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.features.auth.models import OAuthIdentity, User
from src.features.github.models import (
    GitHubAutomationEvent,
    GitHubInstallation,
    GitHubPullRequestLink,
    GitHubStatusAutomation,
    GitHubWebhookDelivery,
    GitHubWebhookOutcome,
)
from src.features.workspaces.models import WorkspaceMember

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


class GitHubWebhookDeliveryRepositoryProtocol(Protocol):
    async def claim(
        self,
        *,
        delivery_id: str,
        event: str,
        action: str | None,
        installation_id: int | None,
    ) -> bool: ...
    async def get(self, delivery_id: str) -> GitHubWebhookDelivery | None: ...
    async def finish(
        self,
        delivery_id: str,
        *,
        outcome: GitHubWebhookOutcome,
        reason: str | None,
        workspace_id: uuid.UUID | None,
    ) -> None: ...


class GitHubPullRequestLinkRepositoryProtocol(Protocol):
    async def list_by_pull_request(
        self, workspace_id: uuid.UUID, pull_request_id: int
    ) -> Sequence[GitHubPullRequestLink]: ...
    async def list_by_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> Sequence[GitHubPullRequestLink]: ...
    async def create(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink: ...
    async def update(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink: ...
    async def delete(self, workspace_id: uuid.UUID, link_ids: Sequence[uuid.UUID]) -> None: ...


@dataclass(frozen=True)
class GitHubSenderMember:
    user_id: uuid.UUID
    name: str


class GitHubStatusAutomationRepositoryProtocol(Protocol):
    async def list_by_workspace(
        self, workspace_id: uuid.UUID
    ) -> Sequence[GitHubStatusAutomation]: ...
    async def get(
        self, workspace_id: uuid.UUID, event: GitHubAutomationEvent
    ) -> GitHubStatusAutomation | None: ...
    async def upsert(
        self,
        workspace_id: uuid.UUID,
        event: GitHubAutomationEvent,
        target_state_id: uuid.UUID | None,
    ) -> None: ...


class GitHubSenderRepositoryProtocol(Protocol):
    async def find_workspace_member(
        self, workspace_id: uuid.UUID, github_user_id: int
    ) -> GitHubSenderMember | None: ...


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


class GitHubWebhookDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(
        self,
        *,
        delivery_id: str,
        event: str,
        action: str | None,
        installation_id: int | None,
    ) -> bool:
        """Grava a entrega se for a primeira vez que este `delivery_id` aparece;
        `False` se já existe. `ON CONFLICT DO NOTHING` na chave primária, e não
        `SELECT` antes do `INSERT`: dois reenvios simultâneos da mesma entrega
        serializam no índice — o segundo espera o commit do primeiro e então cai no
        conflito, em vez de os dois aplicarem o efeito. O `outcome` gravado aqui é
        provisório; `finish` grava o definitivo na mesma transação."""
        stmt = (
            insert(GitHubWebhookDelivery)
            .values(
                delivery_id=delivery_id,
                event=event,
                action=action,
                installation_id=installation_id,
                outcome=GitHubWebhookOutcome.PROCESSED,
            )
            .on_conflict_do_nothing(index_elements=[GitHubWebhookDelivery.delivery_id])
            .returning(GitHubWebhookDelivery.delivery_id)
        )
        inserted = await self._session.scalar(stmt)
        return inserted is not None

    async def get(self, delivery_id: str) -> GitHubWebhookDelivery | None:
        result: GitHubWebhookDelivery | None = await self._session.get(
            GitHubWebhookDelivery, delivery_id
        )
        return result

    async def finish(
        self,
        delivery_id: str,
        *,
        outcome: GitHubWebhookOutcome,
        reason: str | None,
        workspace_id: uuid.UUID | None,
    ) -> None:
        await self._session.execute(
            update(GitHubWebhookDelivery)
            .where(GitHubWebhookDelivery.delivery_id == delivery_id)
            .values(outcome=outcome, reason=reason, workspace_id=workspace_id)
        )


class GitHubPullRequestLinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_pull_request(
        self, workspace_id: uuid.UUID, pull_request_id: int
    ) -> Sequence[GitHubPullRequestLink]:
        stmt = select(GitHubPullRequestLink).where(
            GitHubPullRequestLink.workspace_id == workspace_id,
            GitHubPullRequestLink.pull_request_id == pull_request_id,
        )
        return (await self._session.scalars(stmt)).all()

    async def list_by_issue(
        self, workspace_id: uuid.UUID, issue_id: uuid.UUID
    ) -> Sequence[GitHubPullRequestLink]:
        stmt = (
            select(GitHubPullRequestLink)
            .where(
                GitHubPullRequestLink.workspace_id == workspace_id,
                GitHubPullRequestLink.issue_id == issue_id,
            )
            .order_by(GitHubPullRequestLink.pr_updated_at.desc())
        )
        return (await self._session.scalars(stmt)).all()

    async def create(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink:
        self._session.add(link)
        await self._session.flush()
        return link

    async def update(self, link: GitHubPullRequestLink) -> GitHubPullRequestLink:
        await self._session.flush()
        return link

    async def delete(self, workspace_id: uuid.UUID, link_ids: Sequence[uuid.UUID]) -> None:
        if not link_ids:
            return
        await self._session.execute(
            delete(GitHubPullRequestLink).where(
                GitHubPullRequestLink.workspace_id == workspace_id,
                GitHubPullRequestLink.id.in_(link_ids),
            )
        )


class GitHubStatusAutomationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[GitHubStatusAutomation]:
        # `populate_existing`: o `upsert` é Core e não atualiza objetos que esta
        # sessão já carregou — sem isso, o `PUT` devolveria o valor antigo.
        stmt = (
            select(GitHubStatusAutomation)
            .where(GitHubStatusAutomation.workspace_id == workspace_id)
            .execution_options(populate_existing=True)
        )
        return (await self._session.scalars(stmt)).all()

    async def get(
        self, workspace_id: uuid.UUID, event: GitHubAutomationEvent
    ) -> GitHubStatusAutomation | None:
        stmt = (
            select(GitHubStatusAutomation)
            .where(
                GitHubStatusAutomation.workspace_id == workspace_id,
                GitHubStatusAutomation.event == event,
            )
            .execution_options(populate_existing=True)
        )
        result: GitHubStatusAutomation | None = await self._session.scalar(stmt)
        return result

    async def upsert(
        self,
        workspace_id: uuid.UUID,
        event: GitHubAutomationEvent,
        target_state_id: uuid.UUID | None,
    ) -> None:
        stmt = (
            insert(GitHubStatusAutomation)
            .values(
                id=uuid7(),
                workspace_id=workspace_id,
                event=event,
                target_state_id=target_state_id,
            )
            .on_conflict_do_update(
                index_elements=[GitHubStatusAutomation.workspace_id, GitHubStatusAutomation.event],
                set_={"target_state_id": target_state_id, "updated_at": func.now()},
            )
        )
        await self._session.execute(stmt)


class GitHubSenderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_workspace_member(
        self, workspace_id: uuid.UUID, github_user_id: int
    ) -> GitHubSenderMember | None:
        """Quem fez a ação no GitHub, se for membro ativo do workspace e tiver entrado
        no FlowDesk com a mesma conta do GitHub (`OAuthIdentity`, ADR-061). É a única
        forma de saber que a conta do GitHub é dessa pessoa; e-mail ou login iguais não
        provam nada."""
        stmt = (
            select(User.id, User.name)
            .join(OAuthIdentity, OAuthIdentity.user_id == User.id)
            .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
            .where(
                OAuthIdentity.provider == "github",
                OAuthIdentity.provider_user_id == str(github_user_id),
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return GitHubSenderMember(user_id=row.id, name=row.name)


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
