import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

_PASSWORD_MIN_LENGTH = 10


def _validate_strong_password(password: str) -> str:
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"A senha deve ter ao menos {_PASSWORD_MIN_LENGTH} caracteres.")
    if not re.search(r"[a-z]", password):
        raise ValueError("A senha deve conter ao menos uma letra minúscula.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("A senha deve conter ao menos uma letra maiúscula.")
    if not re.search(r"\d", password):
        raise ValueError("A senha deve conter ao menos um dígito.")
    if not re.search(r"[^\w\s]", password):
        raise ValueError("A senha deve conter ao menos um caractere especial.")
    return password


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("O nome deve ter ao menos 2 caracteres.")
        return stripped

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return _validate_strong_password(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    user: UserResponse


class AccessTokenResponse(BaseModel):
    access_token: str
