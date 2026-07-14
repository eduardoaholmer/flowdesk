import contextlib
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from src.core.config import Settings
from src.core.exceptions import InvalidTokenError

_JWT_ALGORITHM = "RS256"
_VERIFICATION_FAILURES = (VerificationError, InvalidHashError)

_password_hasher = PasswordHasher()

# Hash fixo, computado uma vez no import, usado para igualar o tempo de resposta
# de "usuário não existe" ao de "senha errada" — ver docs/07-security.md §10 e
# ADR-008. O valor em si nunca corresponde a uma senha real de ninguém.
_DUMMY_PASSWORD_HASH = _password_hasher.hash("not-a-real-password-just-for-timing")


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    email: str
    name: str


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: uuid.UUID
    jti: str
    exp: datetime


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except _VERIFICATION_FAILURES:
        return False


def perform_dummy_verification(password: str) -> None:
    """Roda uma verificação Argon2id contra um hash dummy — chamar quando o
    usuário não existe, para que o tempo de resposta não denuncie a diferença
    entre "e-mail inexistente" e "senha errada" (docs/07-security.md §10).
    """
    with contextlib.suppress(*_VERIFICATION_FAILURES):
        _password_hasher.verify(_DUMMY_PASSWORD_HASH, password)


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_private_key_pem, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    try:
        payload = jwt.decode(token, settings.jwt_public_key_pem, algorithms=[_JWT_ALGORITHM])
        return AccessTokenClaims(
            sub=uuid.UUID(payload["sub"]),
            jti=payload["jti"],
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidTokenError() from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
