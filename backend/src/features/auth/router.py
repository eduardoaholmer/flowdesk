import secrets

from fastapi import APIRouter, Depends, Request, Response, status

from src.core.config import Settings, get_settings
from src.core.dependencies import get_current_user
from src.core.schemas import DataEnvelope
from src.core.security import CurrentUser
from src.features.auth.dependencies import get_auth_service
from src.features.auth.exceptions import InvalidRefreshTokenError
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
CSRF_HEADER_NAME = "X-CSRF-Token"
COOKIE_PATH = "/api/v1/auth"


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


def _set_auth_cookies(response: Response, *, refresh_token: str, settings: Settings) -> None:
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        path=COOKIE_PATH,
        httponly=True,
        secure=True,
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
        secure=True,
        samesite="strict",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


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
    _set_auth_cookies(response, refresh_token=result.refresh_token, settings=settings)
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
    _set_auth_cookies(response, refresh_token=result.refresh_token, settings=settings)
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
