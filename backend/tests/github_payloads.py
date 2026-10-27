"""Carrega os payloads reais de `tests/fixtures/github_webhooks/` para os testes do
webhook. `installation_id` troca só o `installation.id` do corpo (o resto fica como
o GitHub manda), e `sign` produz o `X-Hub-Signature-256` correspondente."""

import hashlib
import hmac
import json
from pathlib import Path

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "github_webhooks"


def load_payload(name: str, *, installation_id: int | None = None) -> bytes:
    payload = json.loads((_FIXTURES_DIR / f"{name}.json").read_text())
    if installation_id is not None:
        payload["installation"]["id"] = installation_id
    return json.dumps(payload).encode("utf-8")


def pull_request_payload(
    *,
    installation_id: int,
    action: str = "opened",
    pull_request_id: int = 279147437,
    title: str = "Update the README with new information.",
    body: str | None = "This is a pretty simple change that we need to pull into master.",
    branch: str = "changes",
    draft: bool = False,
    state: str = "open",
    merged: bool = False,
    updated_at: str = "2019-05-15T15:20:33Z",
) -> bytes:
    """`pull_request/opened` real com os campos que o vínculo lê trocados — o resto
    do corpo (dezenas de campos) continua exatamente como o GitHub manda."""
    payload = json.loads((_FIXTURES_DIR / "pull_request_opened.json").read_text())
    payload["action"] = action
    payload["installation"]["id"] = installation_id
    pull_request = payload["pull_request"]
    pull_request.update(
        {
            "id": pull_request_id,
            "title": title,
            "body": body,
            "draft": draft,
            "state": state,
            "merged": merged,
            "updated_at": updated_at,
        }
    )
    pull_request["head"]["ref"] = branch
    return json.dumps(payload).encode("utf-8")


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
