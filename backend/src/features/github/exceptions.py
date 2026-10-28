from src.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class GitHubIntegrationNotConfiguredError(ValidationError):
    """`GITHUB_APP_*` ausente neste ambiente (`core/config.py`) — a integração está
    desligada, não é um erro do usuário."""

    code = "github_integration_not_configured"
    message = "A integração com GitHub não está disponível neste ambiente."


class GitHubConnectStateInvalidError(AuthenticationError):
    """`state` ausente, expirado, já usado ou sem o cookie do navegador que iniciou a
    conexão. Um único `code` para todos os casos, mesmo racional de
    `OAuthProviderError`: não indicar qual checagem específica falhou."""

    code = "github_connect_state_invalid"
    message = "A conexão com o GitHub expirou ou não foi iniciada aqui. Tente novamente."


class GitHubAuthorizationFailedError(AuthenticationError):
    code = "github_authorization_failed"
    message = "Não foi possível confirmar a autorização com o GitHub."


class GitHubInstallationPendingApprovalError(ValidationError):
    """O GitHub devolveu `setup_action=request`: quem instalou não é dono da
    organização, e a instalação espera aprovação. Não há `installation_id` ainda."""

    code = "github_installation_pending_approval"
    message = "A instalação aguarda aprovação de um dono da organização no GitHub."


class GitHubInstallationNotAccessibleError(PermissionDeniedError):
    """O `installation_id` do retorno não está entre as instalações que a conta do
    GitHub autorizada consegue ver — é a checagem que impede ligar ao workspace a
    instalação de outra organização trocando o número na URL (ADR-068)."""

    code = "github_installation_not_accessible"
    message = "Sua conta do GitHub não tem acesso a esta instalação."


class GitHubInstallationAlreadyConnectedError(ConflictError):
    code = "github_installation_already_connected"
    message = "Esta instalação do GitHub já está conectada a outro workspace."


class GitHubInstallationNotFoundError(NotFoundError):
    code = "github_installation_not_found"
    message = "Instalação do GitHub não encontrada."


class GitHubWebhookSignatureInvalidError(AuthenticationError):
    """`X-Hub-Signature-256` ausente, malformado ou divergente do HMAC do corpo —
    ou nenhum `GITHUB_WEBHOOK_SECRET` configurado, caso em que nenhuma entrega pode
    ser autêntica."""

    code = "invalid_webhook_signature"
    message = "Assinatura do webhook inválida."


class GitHubWebhookPayloadTooLargeError(ValidationError):
    """Corpo acima de `GITHUB_WEBHOOK_MAX_BODY_BYTES`, recusado antes do HMAC. 422 e
    não 413: a hierarquia de exceções do `CLAUDE.md` §7 não tem um 413, e o mesmo
    caso de upload já usa 422 (`attachment_too_large`)."""

    code = "github_webhook_payload_too_large"
    message = "Corpo do webhook acima do limite."


class GitHubWebhookPayloadInvalidError(ValidationError):
    """Assinatura válida, mas cabeçalhos `X-GitHub-*` ausentes ou corpo que não é o
    JSON esperado. Só o GitHub consegue chegar aqui, então indica mudança de formato
    do lado dele, não um ataque."""

    code = "invalid_webhook_payload"
    message = "Corpo ou cabeçalhos do webhook em formato inesperado."
