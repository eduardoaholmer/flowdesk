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


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
