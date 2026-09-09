from src.core.exceptions import AuthenticationError, ConflictError, NotFoundError


class InvalidCredentialsError(AuthenticationError):
    """E-mail inexistente ou senha errada — deliberadamente o mesmo `code` para
    os dois casos (`docs/07-security.md` §10, anti-enumeration de e-mail).
    """

    code = "invalid_credentials"
    message = "E-mail ou senha inválidos."


class EmailAlreadyRegisteredError(ConflictError):
    code = "email_already_registered"
    message = "Este e-mail já está cadastrado."


class InvalidRefreshTokenError(AuthenticationError):
    """Cobre todo o espectro de falha em `/auth/refresh`: token ausente, expirado,
    já rotacionado (reuso), sessão revogada, ou CSRF inválido — um único `code`
    genérico para não revelar ao cliente qual checagem específica falhou.
    """

    code = "invalid_refresh_token"
    message = "Sessão inválida ou expirada. Faça login novamente."


class InvalidPasswordResetTokenError(AuthenticationError):
    """Cobre token ausente, desconhecido, expirado ou já usado — mesmo racional
    anti-enumeration de `InvalidRefreshTokenError`: um único `code` genérico não
    revela ao cliente qual checagem específica falhou.
    """

    code = "invalid_password_reset_token"
    message = "Link de recuperação inválido ou expirado. Solicite um novo."


class OAuthProviderNotConfiguredError(NotFoundError):
    """`GOOGLE_CLIENT_ID`/`GITHUB_CLIENT_ID` ausente neste ambiente — o provedor
    está desligado (`core/config.py`), não é um erro do usuário."""

    code = "oauth_provider_not_configured"
    message = "Este provedor de login não está disponível."


class OAuthProviderError(AuthenticationError):
    """Cobre todo o espectro de falha do handshake OAuth: `state` ausente/divergente
    do cookie (possível CSRF), provedor retornou `error=`, troca de `code` por
    token falhou, ou perfil do provedor veio incompleto — um único `code` genérico,
    mesmo racional anti-enumeration de `InvalidRefreshTokenError`."""

    code = "oauth_authentication_failed"
    message = "Não foi possível concluir o login social. Tente novamente."
