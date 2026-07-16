from typing import Protocol

from src.core.logging import get_logger

logger = get_logger(__name__)

_TOKEN_PREVIEW_LENGTH = 6


class MailSender(Protocol):
    async def send_password_reset(self, *, email: str, token: str) -> None: ...


class LoggingMailSender:
    """Placeholder de desenvolvimento para RF-AUTH-06 — não existe infraestrutura de
    e-mail transacional real neste projeto (mesmo racional de ADR-009 para convites
    de workspace: "e-mail transacional... melhoria futura não bloqueante"). Diferente
    do convite, o token de reset nunca pode ser devolvido pela API (quem chama
    `POST /auth/password-reset/request` não é necessariamente o dono do e-mail — ver
    docs/07-security.md §10, anti-enumeration), então este é só um log de correlação:
    o token completo nunca aparece aqui (`CLAUDE.md` §9), só um preview truncado.
    Plugar um `MailSender` real (SES/SendGrid/etc.) é pré-requisito de
    produção real, não deste MVP.
    """

    async def send_password_reset(self, *, email: str, token: str) -> None:
        logger.info(
            "password_reset_email_placeholder",
            email=email,
            token_preview=f"{token[:_TOKEN_PREVIEW_LENGTH]}…",
        )


def get_mail_sender() -> LoggingMailSender:
    return LoggingMailSender()
