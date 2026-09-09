import secrets

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse

from src.core.config import Settings, get_settings
from src.core.dependencies import get_current_user
from src.core.exceptions import FlowDeskError
from src.core.schemas import DataEnvelope
from src.core.security import CurrentUser
from src.features.auth.dependencies import get_auth_service
from src.features.auth.exceptions import InvalidRefreshTokenError, OAuthProviderError
from src.features.auth.oauth_providers import OAuthProvider
from src.features.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"
REMEMBER_COOKIE_NAME = "remember_me"
CSRF_HEADER_NAME = "X-CSRF-Token"
COOKIE_PATH = "/api/v1/auth"

OAUTH_STATE_COOKIE_NAME = "oauth_state"
_OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60


async def verify_csrf_token(request: Request) -> None:
    """Double-submit cookie (`docs/07-security.md` §4): o header precisa bater com
    o cookie `csrf_token`. Mesmo `code` de erro do resto do fluxo de refresh — não
    indicamos ao cliente que a causa específica foi CSRF, e não autenticação.
    """
    header_value = request.headers.get(CSRF_HEADER_NAME)
    cookie_value = request.cookies.get(CSRF_COOKIE_NAME)
    if (
        not header_value
        or not cookie_value
        or not secrets.compare_digest(header_value, cookie_value)
    ):
        raise InvalidRefreshTokenError()


def _set_auth_cookies(
    response: Response, *, refresh_token: str, settings: Settings, remember_me: bool
) -> None:
    # `max_age=None` produz um cookie de sessão (apagado ao fechar o navegador) —
    # é assim que "Lembrar de mim" desmarcado se traduz em cookie: o refresh token
    # continua válido no banco pelos mesmos `refresh_token_expire_days`, só o
    # navegador não retém o cookie além da sessão atual.
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60 if remember_me else None
    # `secure=True` incondicional derrubava silenciosamente o cookie em dev
    # (http://localhost, sem TLS) — o navegador nunca chega a armazená-lo, então
    # todo reload perdia a sessão. Só exigimos `Secure` em produção (https real).
    secure = settings.is_production
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        path=COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite="strict",
    )
    # Path="/" (não COOKIE_PATH): este cookie só existe para o frontend ler via
    # `document.cookie` (docs/07-security.md §4) e ecoar no header X-CSRF-Token —
    # como o SPA vive em rotas fora de /api/v1/auth, um Path restrito o tornaria
    # invisível para o próprio JavaScript que precisa lê-lo.
    response.set_cookie(
        CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        max_age=max_age,
        path="/",
        httponly=False,
        secure=secure,
        samesite="strict",
    )
    # Marcador lido em `/auth/refresh` (que não recebe o payload de login de novo)
    # para que a escolha de "Lembrar de mim" sobreviva à rotação do refresh token.
    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        "1" if remember_me else "0",
        max_age=max_age,
        path=COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite="strict",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
    response.delete_cookie(REMEMBER_COOKIE_NAME, path=COOKIE_PATH)


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=DataEnvelope[UserResponse]
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> DataEnvelope[UserResponse]:
    user = await service.register(payload)
    return DataEnvelope(data=UserResponse.model_validate(user))


@router.post("/login", response_model=DataEnvelope[TokenResponse])
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[TokenResponse]:
    result = await service.login(
        payload.email,
        payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_auth_cookies(
        response,
        refresh_token=result.refresh_token,
        settings=settings,
        remember_me=payload.remember_me,
    )
    token_response = TokenResponse(
        access_token=result.access_token, user=UserResponse.model_validate(result.user)
    )
    return DataEnvelope(data=token_response)


@router.post(
    "/refresh",
    response_model=DataEnvelope[AccessTokenResponse],
    dependencies=[Depends(verify_csrf_token)],
)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[AccessTokenResponse]:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token is None:
        raise InvalidRefreshTokenError()

    result = await service.refresh(refresh_token)
    remember_me = request.cookies.get(REMEMBER_COOKIE_NAME) == "1"
    _set_auth_cookies(
        response, refresh_token=result.refresh_token, settings=settings, remember_me=remember_me
    )
    return DataEnvelope(data=AccessTokenResponse(access_token=result.access_token))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> None:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    await service.logout(refresh_token)
    _clear_auth_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout_all(current_user.id)
    _clear_auth_cookies(response)


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    payload: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    """202, sempre — não 200/404 conforme o e-mail exista ou não (anti-enumeration,
    `docs/07-security.md` §10). O corpo da resposta nunca carrega o token; ver
    `core/mail.py::MailSender`."""
    await service.request_password_reset(payload.email)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.confirm_password_reset(payload.token, payload.new_password)


@router.get("/{provider}/login")
async def oauth_login(
    provider: OAuthProvider,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Início do Authorization Code flow: redireciona o navegador para o provedor.

    `state` é gerado aqui e guardado em cookie próprio (nunca no cookie de CSRF do
    resto do fluxo — semânticas de proteção diferentes) para o `callback` comparar
    depois; `SameSite=Lax` (não `Strict`, diferente dos outros cookies deste
    router) porque este cookie precisa sobreviver à navegação de nível superior de
    volta ao nosso domínio vinda de `accounts.google.com`/`github.com` — um cookie
    `Strict` seria descartado pelo navegador nesse retorno. Mesma exceção à regra de
    "rota não trata exceção" do `callback` abaixo, pelo mesmo motivo: um provedor
    desligado neste ambiente (`OAuthProviderNotConfiguredError`) também precisa
    virar um redirect de volta à SPA, não um JSON cru na aba do navegador.
    """
    state = secrets.token_urlsafe(32)
    try:
        authorize_url = service.build_oauth_authorize_url(provider, state)
    except FlowDeskError as exc:
        return RedirectResponse(
            f"{settings.frontend_base_url}/oauth/callback?error={exc.code}",
            status_code=status.HTTP_302_FOUND,
        )

    response = RedirectResponse(authorize_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        OAUTH_STATE_COOKIE_NAME,
        state,
        max_age=_OAUTH_STATE_MAX_AGE_SECONDS,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return response


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: OAuthProvider,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Fim do Authorization Code flow.

    Diferente de toda outra rota deste router, aqui a exceção de domínio é
    capturada manualmente (não sobe para o exception handler global, CLAUDE.md
    §7/§4) — de propósito: quem chega aqui é o navegador fazendo uma navegação de
    página inteira vinda do provedor, não um cliente JS lendo um envelope JSON.
    Deixar a exceção subir devolveria um JSON cru numa aba do navegador; em vez
    disso traduzimos para um redirect de volta à SPA com o `code` do erro na
    query string, que é quem sabe mostrar isso decentemente ao usuário.
    """
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    try:
        state_is_valid = (
            state is not None
            and cookie_state is not None
            and secrets.compare_digest(state, cookie_state)
        )
        if error or not code or not state_is_valid:
            raise OAuthProviderError()

        result = await service.login_with_oauth(
            provider,
            code,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except FlowDeskError as exc:
        redirect = RedirectResponse(
            f"{settings.frontend_base_url}/oauth/callback?error={exc.code}",
            status_code=status.HTTP_302_FOUND,
        )
        redirect.delete_cookie(OAUTH_STATE_COOKIE_NAME, path=COOKIE_PATH)
        return redirect

    response = RedirectResponse(
        f"{settings.frontend_base_url}/oauth/callback", status_code=status.HTTP_302_FOUND
    )
    # Não há um checkbox de "lembrar de mim" neste fluxo (não passa por um
    # formulário) — login social sempre se comporta como se estivesse marcado.
    _set_auth_cookies(
        response, refresh_token=result.refresh_token, settings=settings, remember_me=True
    )
    response.delete_cookie(OAUTH_STATE_COOKIE_NAME, path=COOKIE_PATH)
    return response
