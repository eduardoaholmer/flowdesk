from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chave pública de DEV do par gerado só para desenvolvimento local (`.env.example`,
# `docs/09-decision-log.md` ADR-008) — nunca deveria aparecer em um ambiente de
# produção. Comparada em `_forbid_dev_key_in_production` abaixo para transformar esse
# risco documentado em uma falha de inicialização real, não só um comentário.
_DEV_JWT_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr0FxunGNtYrO+OQT8vmb\n"
    "OdG4+rO1XClx/d+X5K/2u8415yxNU3l9k5fP2W0gO4DzXA/IbcuJ5qpK19HOc30E\n"
    "7DB5JkeA0ZaJNEDspCMoXcHcj5d1nWxMgF1OkpXd0lSX2nf40rh4IoYnn4gFRL21\n"
    "TOdF+5D9fvNtqNFxtJjQEOryAt+MQvhPbpmuPulYAxP+d21rXFNAdWiFMD9/yt89\n"
    "MnoLYLJ9GUMwk5GcPRMl73mYvQcZE8YRJMLYKjzGpmE1vfGz3UGEDGCg8GNh95Wr\n"
    "Do4Ri+7wgQDv7cFOqu4iILLMdcGK1r3s2BmiDru7oVtaAdIlH41KDQrCHgZrhIAC\n"
    "AQIDAQAB\n"
    "-----END PUBLIC KEY-----"
)


class Settings(BaseSettings):
    """Configuração da aplicação, carregada de variáveis de ambiente.

    Falha na inicialização (não no primeiro uso) se uma variável obrigatória
    estiver ausente — preferimos um crash imediato e claro a um erro tardio
    e difícil de rastrear em produção.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_version: str = "0.1.0"

    database_url: str
    redis_url: str

    # Mantido como string simples (não list[str]) porque pydantic-settings tenta
    # decodificar JSON para tipos complexos vindos de variável de ambiente/.env —
    # incompatível com o formato "a, b, c" que .env files usam na prática.
    cors_origins_raw: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    # PEM com quebras de linha escapadas (`\n` literal) em vez de multilinha real —
    # o mesmo valor funciona sem sintaxe especial tanto em ".env" quanto no bloco
    # `env:` do GitHub Actions, que não suporta valor multilinha sem heredoc.
    jwt_private_key: str
    jwt_public_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    invitation_expire_days: int = 7
    # Curta de propósito (RF-AUTH-06): bem menor que refresh (30 dias) ou convite
    # (7 dias) — a janela de exposição de um token que dá controle total da conta
    # deve ser a menor praticável (docs/07-security.md).
    password_reset_token_expire_minutes: int = 30

    # Armazenamento de anexos — `core/storage.py::StorageProvider` é o ponto de
    # extensão, `storage_provider` escolhe qual implementação `get_storage_provider()`
    # devolve (Sprint 17.2/M6, ADR-038). "local" (default) grava em disco —
    # `upload_dir` é path relativo resolvido a partir do cwd do processo, mesmo
    # racional de `database_url` não ser hardcoded. "s3" usa um bucket
    # S3-compatible (AWS S3, MinIO, R2, Spaces); credenciais NUNCA são um campo
    # deste `Settings` — vêm da cadeia padrão de credenciais do boto3
    # (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`/IAM role),
    # o SDK já resolve isso corretamente sem duplicar a lógica aqui.
    storage_provider: Literal["local", "s3"] = "local"
    upload_dir: str = "var/uploads"
    s3_bucket_name: str | None = None
    s3_region: str = "us-east-1"
    # Non-None só para provider S3-compatible que não é AWS (MinIO, R2, Spaces) —
    # AWS S3 real resolve o endpoint a partir de `s3_region` e não precisa disso.
    s3_endpoint_url: str | None = None
    max_upload_size_bytes: int = 10 * 1024 * 1024
    # Lista branca por tipo de conteúdo (não extensão de arquivo, que é
    # facilmente forjável) — mesmo formato de `cors_origins_raw`, string
    # "a, b, c" em vez de lista JSON (pydantic-settings não decodifica JSON de
    # variável de ambiente/.env de forma confiável para tipos complexos).
    allowed_upload_content_types_raw: str = Field(
        default=(
            "image/png,image/jpeg,image/gif,image/webp,image/svg+xml,"
            "application/pdf,text/plain,text/csv,"
            "application/zip,application/msword,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
            "application/vnd.ms-excel,"
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        alias="ALLOWED_UPLOAD_CONTENT_TYPES",
    )

    # E-mail transacional — `core/mail.py::MailSender` é o ponto de extensão,
    # `mail_provider` escolhe qual implementação `get_mail_sender()` devolve
    # (Sprint 17.3/M6, ADR-039). "logging" (default) só loga um preview
    # truncado do token (`CLAUDE.md` §9) — nenhum e-mail real sai. "smtp" usa
    # `smtplib` (stdlib, síncrono envolvido em `asyncio.to_thread`, mesmo
    # padrão do `S3StorageProvider`) contra um servidor SMTP real. Diferente de
    # `s3_*`, credenciais SMTP viram campo deste `Settings` — não existe uma
    # cadeia de credenciais padrão de indústria para SMTP genérico como a do
    # boto3 para AWS.
    mail_provider: Literal["logging", "smtp"] = "logging"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    # Base do link enviado por e-mail (`{frontend_base_url}/reset-password/{token}`,
    # `frontend/src/shared/lib/routes.ts::resetPasswordRoute`) — mesmo default de
    # `cors_origins_raw` para o ambiente local.
    frontend_base_url: str = "http://localhost:5173"

    @property
    def allowed_upload_content_types(self) -> frozenset[str]:
        return frozenset(
            t.strip() for t in self.allowed_upload_content_types_raw.split(",") if t.strip()
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def jwt_private_key_pem(self) -> str:
        return self.jwt_private_key.replace("\\n", "\n")

    @property
    def jwt_public_key_pem(self) -> str:
        return self.jwt_public_key.replace("\\n", "\n")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _forbid_dev_key_in_production(self) -> "Settings":
        """ADR-008 documenta o risco de reusar o par de chaves de DEV em produção — aqui
        isso vira uma falha de inicialização real (`CLAUDE.md` §6), não só um comentário.
        """
        if self.is_production and self.jwt_public_key_pem.strip() == _DEV_JWT_PUBLIC_KEY.strip():
            raise ValueError(
                "ENVIRONMENT=production não pode usar o par de chaves JWT de "
                "desenvolvimento (ver docs/09-decision-log.md ADR-008). Gere um par "
                "novo antes de subir este ambiente."
            )
        return self

    @model_validator(mode="after")
    def _require_s3_bucket_when_s3_provider(self) -> "Settings":
        """Mesmo racional de `_forbid_dev_key_in_production`: falha na inicialização,
        não no primeiro upload — `STORAGE_PROVIDER=s3` sem bucket configurado é um
        erro de configuração, não uma condição de runtime recuperável.
        """
        if self.storage_provider == "s3" and not self.s3_bucket_name:
            raise ValueError("STORAGE_PROVIDER=s3 exige S3_BUCKET_NAME configurado.")
        return self

    @model_validator(mode="after")
    def _require_smtp_config_when_smtp_provider(self) -> "Settings":
        if self.mail_provider == "smtp" and not (self.smtp_host and self.smtp_from_email):
            raise ValueError("MAIL_PROVIDER=smtp exige SMTP_HOST e SMTP_FROM_EMAIL configurados.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
