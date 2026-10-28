from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlencode

import httpx

from src.core.logging import get_logger
from src.features.github.exceptions import GitHubAuthorizationFailedError

logger = get_logger(__name__)

_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_API_URL = "https://api.github.com"
_HTTP_TIMEOUT_SECONDS = 10.0
_INSTALLATIONS_PAGE_SIZE = 100
# Uma conta com mais de 1.000 instalações acessíveis do mesmo app não é um caso
# real; o teto só impede que uma resposta malformada vire um laço sem fim.
_MAX_INSTALLATION_PAGES = 10


@dataclass(frozen=True)
class GitHubInstallationInfo:
    installation_id: int
    account_login: str
    account_type: str
    suspended_at: datetime | None


class GitHubAppClientProtocol(Protocol):
    def installation_url(self, state: str) -> str: ...
    async def find_user_installation(
        self, code: str, installation_id: int
    ) -> GitHubInstallationInfo | None: ...


class GitHubAppClient:
    def __init__(self, *, slug: str, client_id: str, client_secret: str) -> None:
        self._slug = slug
        self._client_id = client_id
        self._client_secret = client_secret

    def installation_url(self, state: str) -> str:
        query = urlencode({"state": state})
        return f"https://github.com/apps/{self._slug}/installations/new?{query}"

    async def find_user_installation(
        self, code: str, installation_id: int
    ) -> GitHubInstallationInfo | None:
        """Prova de posse da instalação (ADR-068): troca o `code` do retorno por um
        token de usuário e procura `installation_id` entre as instalações que esse
        usuário enxerga. `None` quando ele não tem acesso a ela. O token só vive
        nesta chamada e é revogado ao final; nada dele é guardado."""
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as http_client:
            user_token = await self._exchange_code(http_client, code)
            try:
                return await self._find_installation(http_client, user_token, installation_id)
            finally:
                await self._revoke_token(http_client, user_token)

    async def _exchange_code(self, http_client: httpx.AsyncClient, code: str) -> str:
        try:
            response = await http_client.post(
                _GITHUB_TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            # Código inválido ou expirado volta como 200 com `error` no corpo, sem
            # `access_token` — o `KeyError` abaixo cobre esse caso.
            return str(response.json()["access_token"])
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise GitHubAuthorizationFailedError() from exc

    async def _find_installation(
        self, http_client: httpx.AsyncClient, user_token: str, installation_id: int
    ) -> GitHubInstallationInfo | None:
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            for page in range(1, _MAX_INSTALLATION_PAGES + 1):
                response = await http_client.get(
                    f"{_GITHUB_API_URL}/user/installations",
                    params={"per_page": _INSTALLATIONS_PAGE_SIZE, "page": page},
                    headers=headers,
                )
                response.raise_for_status()
                installations = response.json()["installations"]
                for entry in installations:
                    if entry["id"] == installation_id:
                        return _parse_installation(entry)
                if len(installations) < _INSTALLATIONS_PAGE_SIZE:
                    return None
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise GitHubAuthorizationFailedError() from exc
        return None

    async def _revoke_token(self, http_client: httpx.AsyncClient, user_token: str) -> None:
        """Melhor esforço: a conexão já foi decidida, e o token de usuário de um
        GitHub App expira sozinho em 8 horas. Uma falha aqui fica no log em vez de
        derrubar uma conexão válida."""
        try:
            response = await http_client.request(
                "DELETE",
                f"{_GITHUB_API_URL}/applications/{self._client_id}/token",
                auth=(self._client_id, self._client_secret),
                json={"access_token": user_token},
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("github_user_token_revoke_failed", error=type(exc).__name__)


def _parse_installation(entry: dict[str, object]) -> GitHubInstallationInfo:
    account = entry["account"]
    if not isinstance(account, dict):
        raise ValueError("installation.account ausente")
    suspended_at = entry.get("suspended_at")
    return GitHubInstallationInfo(
        installation_id=int(str(entry["id"])),
        account_login=str(account["login"]),
        account_type=str(account["type"]),
        suspended_at=(
            datetime.fromisoformat(suspended_at) if isinstance(suspended_at, str) else None
        ),
    )
