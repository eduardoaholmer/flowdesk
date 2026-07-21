import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from src.core.mail import SMTPMailSender

# Env vars dedicadas deste teste, independentes de `MAIL_PROVIDER`/`SMTP_*` do
# `Settings` da aplicação (que continua "logging" por padrão em todo o resto da
# suíte) — exercitam `SMTPMailSender` contra um MailHog efêmero (mesmo padrão
# já usado para MinIO na Sprint 17.2: serviço real em container, não mock).
_SMTP_HOST = os.environ.get("SMTP_TEST_HOST", "localhost")
_SMTP_PORT = int(os.environ.get("SMTP_TEST_PORT", "1025"))
_MAILHOG_API_URL = os.environ.get("MAILHOG_API_URL", "http://localhost:8025")


@pytest.fixture
def sender() -> SMTPMailSender:
    return SMTPMailSender(
        host=_SMTP_HOST,
        port=_SMTP_PORT,
        username=None,
        password=None,
        from_email="noreply@flowdesk.test",
        use_tls=False,  # MailHog não expõe STARTTLS
        frontend_base_url="http://localhost:5173",
    )


@pytest.fixture(autouse=True)
async def _clear_mailbox() -> AsyncGenerator[None, None]:
    async with httpx.AsyncClient(base_url=_MAILHOG_API_URL) as client:
        await client.delete("/api/v1/messages")
    yield


async def _fetch_latest_message() -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=_MAILHOG_API_URL) as client:
        response = await client.get("/api/v2/messages")
        response.raise_for_status()
        items: list[dict[str, Any]] = response.json()["items"]
        assert items, "nenhuma mensagem chegou ao MailHog"
        return items[0]


async def test_send_password_reset_delivers_email_with_reset_link(
    sender: SMTPMailSender,
) -> None:
    email = "ada@example.com"
    token = "test-token-123"

    await sender.send_password_reset(email=email, token=token)

    message = await _fetch_latest_message()
    assert message["Content"]["Headers"]["To"] == [email]
    body = message["Content"]["Body"]
    assert f"http://localhost:5173/reset-password/{token}" in body
