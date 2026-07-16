from src.core.exceptions import AuthenticationError, ConflictError


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
