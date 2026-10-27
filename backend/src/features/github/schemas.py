import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.features.github.models import GitHubInstallation


@dataclass(frozen=True)
class GitHubIntegrationStatus:
    configured: bool
    installations: Sequence[GitHubInstallation]


@dataclass(frozen=True)
class GitHubConnectionStart:
    install_url: str
    state: str


class GitHubInstallationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    installation_id: int
    account_login: str
    account_type: str
    connected_by_id: uuid.UUID
    suspended_at: datetime | None
    created_at: datetime


class GitHubIntegrationResponse(BaseModel):
    configured: bool
    installations: list[GitHubInstallationResponse]

    @classmethod
    def from_status(cls, status: GitHubIntegrationStatus) -> "GitHubIntegrationResponse":
        return cls(
            configured=status.configured,
            installations=[
                GitHubInstallationResponse.model_validate(installation)
                for installation in status.installations
            ],
        )


class GitHubConnectResponse(BaseModel):
    install_url: str
