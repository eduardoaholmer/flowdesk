import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(default=None)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


# Único case-insensitive por função — o schema HTTP (Sprint 3+) ainda não existe
# para normalizar o e-mail de entrada, então a garantia vive no banco desde já.
Index("ix_users_email_lower", func.lower(User.email), unique=True)


class Session(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Um login/dispositivo. Ver docs/03-database.md — entidade nova entre User e RefreshToken.

    Revogar a sessão (logout) é o ponto central de controle: um refresh token só é
    aceito se a sessão a que pertence ainda não foi revogada.
    """

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id_revoked_at", "user_id", "revoked_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(default=None)
    ip_address: Mapped[str | None] = mapped_column(default=None)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped[User] = relationship(back_populates="sessions")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="session")


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Token opaco rotativo (docs/07-security.md §2) — pertence a uma Session, não ao User direto.

    `replaced_by_id` mantém a cadeia de rotação: se um token já substituído for
    reapresentado, isso indica reuso/roubo e toda a cadeia da sessão deve ser revogada.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_session_id", "session_id"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="RESTRICT"), default=None
    )

    session: Mapped[Session] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """RF-AUTH-06. Uso único (`used_at`, não uma cadeia de rotação como
    `RefreshToken.replaced_by_id` — não há "próximo" token, só emitir um novo do
    zero) e vida curta (`Settings.password_reset_token_expire_minutes`, ver
    `core/config.py`). Descartável, sem valor histórico após expirar/usar — mesmo
    racional de soft-delete-dispensado de `Notification` (docs/03-database.md §2).
    """

    __tablename__ = "password_reset_tokens"
    __table_args__ = (Index("ix_password_reset_tokens_user_id", "user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
