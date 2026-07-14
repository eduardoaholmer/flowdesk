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
