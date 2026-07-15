import pytest
from pydantic import ValidationError
from src.core.config import Settings

_DEV_JWT_PUBLIC_KEY_RAW = (
    "-----BEGIN PUBLIC KEY-----\\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr0FxunGNtYrO+OQT8vmb\\n"
    "OdG4+rO1XClx/d+X5K/2u8415yxNU3l9k5fP2W0gO4DzXA/IbcuJ5qpK19HOc30E\\n"
    "7DB5JkeA0ZaJNEDspCMoXcHcj5d1nWxMgF1OkpXd0lSX2nf40rh4IoYnn4gFRL21\\n"
    "TOdF+5D9fvNtqNFxtJjQEOryAt+MQvhPbpmuPulYAxP+d21rXFNAdWiFMD9/yt89\\n"
    "MnoLYLJ9GUMwk5GcPRMl73mYvQcZE8YRJMLYKjzGpmE1vfGz3UGEDGCg8GNh95Wr\\n"
    "Do4Ri+7wgQDv7cFOqu4iILLMdcGK1r3s2BmiDru7oVtaAdIlH41KDQrCHgZrhIAC\\n"
    "AQIDAQAB\\n"
    "-----END PUBLIC KEY-----"
)

_BASE_KWARGS = {
    "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
    "redis_url": "redis://localhost:6379/0",
    "jwt_private_key": "not-a-real-key",
}


def test_production_with_dev_jwt_key_raises() -> None:
    with pytest.raises(ValidationError, match="ADR-008"):
        Settings(
            **_BASE_KWARGS,
            environment="production",
            jwt_public_key=_DEV_JWT_PUBLIC_KEY_RAW,
        )


def test_production_with_a_different_key_is_allowed() -> None:
    settings = Settings(
        **_BASE_KWARGS,
        environment="production",
        jwt_public_key="-----BEGIN PUBLIC KEY-----\\nnot-the-dev-key\\n-----END PUBLIC KEY-----",
    )

    assert settings.is_production


def test_development_with_dev_jwt_key_is_allowed() -> None:
    settings = Settings(
        **_BASE_KWARGS,
        environment="development",
        jwt_public_key=_DEV_JWT_PUBLIC_KEY_RAW,
    )

    assert not settings.is_production


def test_invalid_environment_value_raises() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **_BASE_KWARGS,
            environment="produciton",
            jwt_public_key=_DEV_JWT_PUBLIC_KEY_RAW,
        )
