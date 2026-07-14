from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, carregada de variáveis de ambiente.

    Falha na inicialização (não no primeiro uso) se uma variável obrigatória
    estiver ausente — preferimos um crash imediato e claro a um erro tardio
    e difícil de rastrear em produção.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
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

    # Armazenamento local de anexos (Sprint 8) — `core/storage.py::StorageProvider`
    # é o ponto de extensão para trocar por S3/equivalente sem mudar o contrato
    # de `AttachmentService`. Path relativo resolvido a partir do cwd do processo
    # (mesmo racional de `database_url` não ser hardcoded).
    upload_dir: str = "var/uploads"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
