from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from urllib.parse import urlencode

import httpx

from src.features.auth.exceptions import OAuthProviderError

_GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
_GOOGLE_SCOPE = "openid email profile"

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
_GITHUB_SCOPE = "read:user user:email"

_HTTP_TIMEOUT_SECONDS = 10.0


class OAuthProvider(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"


@dataclass(frozen=True)
class OAuthProfile:
    """Formato normalizado, igual para os dois provedores — o resto do domínio
    (`AuthService.login_with_oauth`) nunca precisa saber a forma bruta da resposta
    de Google ou GitHub."""

    provider: OAuthProvider
    provider_user_id: str
    email: str
    name: str
    avatar_url: str | None


class OAuthClientProtocol(Protocol):
    def authorize_url(self, state: str) -> str: ...
    async def fetch_profile(self, code: str) -> OAuthProfile: ...


class GoogleOAuthClient:
    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": _GOOGLE_SCOPE,
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{_GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"

    async def fetch_profile(self, code: str) -> OAuthProfile:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as http_client:
            try:
                token_response = await http_client.post(
                    _GOOGLE_TOKEN_URL,
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": self._redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_response.raise_for_status()
                access_token = token_response.json()["access_token"]

                userinfo_response = await http_client.get(
                    _GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                userinfo_response.raise_for_status()
                payload = userinfo_response.json()
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise OAuthProviderError() from exc

        email = payload.get("email")
        subject = payload.get("sub")
        if not email or not subject:
            raise OAuthProviderError()

        return OAuthProfile(
            provider=OAuthProvider.GOOGLE,
            provider_user_id=str(subject),
            email=email,
            name=payload.get("name") or email,
            avatar_url=payload.get("picture"),
        )


class GitHubOAuthClient:
    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": _GITHUB_SCOPE,
            "state": state,
        }
        return f"{_GITHUB_AUTHORIZE_URL}?{urlencode(params)}"

    async def fetch_profile(self, code: str) -> OAuthProfile:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as http_client:
            try:
                token_response = await http_client.post(
                    _GITHUB_TOKEN_URL,
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": self._redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
                token_response.raise_for_status()
                access_token = token_response.json()["access_token"]

                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                }
                user_response = await http_client.get(_GITHUB_USER_URL, headers=headers)
                user_response.raise_for_status()
                user_payload = user_response.json()

                email = user_payload.get("email")
                if not email:
                    # GitHub omite o e-mail em `/user` quando a pessoa marcou o e-mail
                    # como privado — precisa do endpoint dedicado para achar o
                    # primário verificado (`docs/07-security.md`: só e-mail
                    # verificado pelo provedor autoriza find-or-create/link).
                    emails_response = await http_client.get(_GITHUB_EMAILS_URL, headers=headers)
                    emails_response.raise_for_status()
                    email = _primary_verified_email(emails_response.json())
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise OAuthProviderError() from exc

        subject = user_payload.get("id")
        if not email or subject is None:
            raise OAuthProviderError()

        return OAuthProfile(
            provider=OAuthProvider.GITHUB,
            provider_user_id=str(subject),
            email=email,
            name=user_payload.get("name") or user_payload.get("login") or email,
            avatar_url=user_payload.get("avatar_url"),
        )


def _primary_verified_email(emails: list[dict[str, object]]) -> str | None:
    for entry in emails:
        if entry.get("primary") and entry.get("verified"):
            return str(entry["email"])
    for entry in emails:
        if entry.get("verified"):
            return str(entry["email"])
    return None
