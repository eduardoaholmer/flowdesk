import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from src.core.config import Settings
from src.core.exceptions import InvalidTokenError
from src.core.security import (
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    perform_dummy_verification,
    verify_password,
)


def test_hash_password_roundtrip() -> None:
    password = "Str0ng!Passw0rd"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("Str0ng!Passw0rd")

    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("whatever", "not-a-real-argon2-hash") is False


def test_perform_dummy_verification_never_raises() -> None:
    perform_dummy_verification("any-password")


def test_generate_refresh_token_is_unique() -> None:
    assert generate_refresh_token() != generate_refresh_token()


def test_hash_refresh_token_is_deterministic() -> None:
    token = generate_refresh_token()

    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_hash_refresh_token_differs_for_different_tokens() -> None:
    assert hash_refresh_token("a") != hash_refresh_token("b")


def test_generate_csrf_token_is_unique() -> None:
    assert generate_csrf_token() != generate_csrf_token()


def test_create_and_decode_access_token_roundtrip(settings: Settings) -> None:
    user_id = uuid.uuid4()

    token = create_access_token(user_id, settings)
    claims = decode_access_token(token, settings)

    assert claims.sub == user_id
    assert claims.jti


def test_decode_access_token_rejects_expired_token(settings: Settings) -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": now - timedelta(minutes=30),
        "exp": now - timedelta(minutes=15),
        "jti": uuid.uuid4().hex,
    }
    expired_token = jwt.encode(payload, settings.jwt_private_key_pem, algorithm="RS256")

    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token, settings)


def test_decode_access_token_rejects_wrong_signature(settings: Settings) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_private_pem = other_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "jti": uuid.uuid4().hex,
    }
    token_signed_by_someone_else = jwt.encode(payload, other_private_pem, algorithm="RS256")

    with pytest.raises(InvalidTokenError):
        decode_access_token(token_signed_by_someone_else, settings)


def test_decode_access_token_rejects_malformed_token(settings: Settings) -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-real-token", settings)
