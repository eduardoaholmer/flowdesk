from collections.abc import Generator

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from src.core.config import Settings


def _generate_rsa_pem_pair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture(scope="session")
def rsa_keypair() -> Generator[tuple[str, str], None, None]:
    yield _generate_rsa_pem_pair()


@pytest.fixture
def settings(rsa_keypair: tuple[str, str]) -> Settings:
    """`Settings` isolado para testes unitários — chaves RS256 geradas em memória,
    nunca as chaves reais de dev/produção (esses testes não sobem banco/Redis).
    """
    private_pem, public_pem = rsa_keypair
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        jwt_private_key=private_pem,
        jwt_public_key=public_pem,
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
    )
