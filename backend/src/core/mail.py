import asyncio
import smtplib
from email.message import EmailMessage
from typing import Protocol

from src.core.config import Settings, get_settings
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
    """

    async def send_password_reset(self, *, email: str, token: str) -> None:
        logger.info(
            "password_reset_email_placeholder",
            email=email,
            token_preview=f"{token[:_TOKEN_PREVIEW_LENGTH]}…",
        )


class SMTPMailSender:
    """Envio real via `smtplib` (stdlib, síncrono — envolvido em `asyncio.to_thread`,
    mesmo padrão já usado por `S3StorageProvider` para I/O bloqueante, Sprint 17.2/M6)
    — sem dependência nova (Sprint 17.3/M6, ADR-039).

    Diferente de `LoggingMailSender`, o corpo do e-mail carrega o token completo:
    não é uma violação do anti-enumeration de `docs/07-security.md` §10/§15 — o
    destinatário do e-mail é justamente quem tem posse legítima daquele endereço,
    o mesmo dado que `AuthService.request_password_reset` já usou para decidir
    enviar. O log desta classe nunca inclui o token nem a senha SMTP (`CLAUDE.md`
    §9), só o e-mail de destino.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str,
        use_tls: bool,
        frontend_base_url: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls
        self._frontend_base_url = frontend_base_url

    def _send_sync(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port) as client:
            if self._use_tls:
                client.starttls()
            if self._username and self._password:
                client.login(self._username, self._password)
            client.send_message(message)

    async def send_password_reset(self, *, email: str, token: str) -> None:
        reset_link = f"{self._frontend_base_url}/reset-password/{token}"
        message = EmailMessage()
        message["Subject"] = "Redefinição de senha — FlowDesk"
        message["From"] = self._from_email
        message["To"] = email
        message.set_content(
            "Recebemos uma solicitação para redefinir sua senha no FlowDesk.\n\n"
            f"Para continuar, acesse: {reset_link}\n\n"
            "Se você não solicitou isso, ignore este e-mail — sua senha "
            "permanece inalterada."
        )

        await asyncio.to_thread(self._send_sync, message)
        logger.info("password_reset_email_sent", email=email)


def get_mail_sender(settings: Settings | None = None) -> MailSender:
    settings = settings or get_settings()
    if settings.mail_provider == "smtp":
        assert settings.smtp_host is not None  # já validado por Settings na inicialização
        assert settings.smtp_from_email is not None
        return SMTPMailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
            frontend_base_url=settings.frontend_base_url,
        )
    return LoggingMailSender()
