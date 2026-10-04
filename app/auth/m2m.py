"""Identidade confidencial e concessão mínima de scopes para laboratório."""
from typing import Annotated
from urllib.parse import unquote_plus
from secrets import compare_digest
import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2, SecurityScopes
from fastapi.responses import JSONResponse
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowClientCredentials
from app.auth.dependencies import SettingsDep
from app.auth.passwords import verificar_senha
from app.auth.tokens import DISPONIBILIDADE_SCOPE, validar_token_m2m
from app.settings import Settings

class OAuthClientError(HTTPException):
    def __init__(self, error: str, status_code: int = 400):
        headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}
        if status_code == 401:
            headers["WWW-Authenticate"] = "Basic"
        super().__init__(status_code, {"error": error}, headers=headers)


class OAuthClientBasic(HTTPBasic):
    async def __call__(self, request: Request) -> HTTPBasicCredentials | None:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise OAuthClientError("invalid_client", 401) from None


client_basic = OAuthClientBasic(auto_error=False, scheme_name="ClientCredentialsAuthentication")
client_bearer = OAuth2(
    flows=OAuthFlowsModel(clientCredentials=OAuthFlowClientCredentials(
        tokenUrl="auth/m2m/token",
        scopes={DISPONIBILIDADE_SCOPE: "Ler intervalos livres sem dados de pacientes"},
    )),
    scheme_name="LaboratorioOAuth2", auto_error=False,
)

def oauth_error_response(_request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, OAuthClientError):
        raise error
    return JSONResponse(error.detail, status_code=error.status_code, headers=error.headers)


def autenticar_cliente(credentials: Annotated[HTTPBasicCredentials | None, Depends(client_basic)],
                       request: Request, settings: SettingsDep) -> None:
    client_id = unquote_plus(credentials.username) if credentials else ""
    secret = unquote_plus(credentials.password) if credentials else ""
    esperado = settings.m2m_client_secret_hash
    hash_value = esperado.get_secret_value() if esperado else request.app.state.dummy_hash
    valido = verificar_senha(secret, hash_value)
    if credentials is None or esperado is None or not compare_digest(client_id.encode(), settings.m2m_client_id.encode()) or not valido:
        raise OAuthClientError("invalid_client", 401)


def identidade_laboratorio(authorization: str | None, settings: Settings) -> dict:
    try:
        if authorization is None:
            raise jwt.InvalidTokenError()
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or settings.m2m_client_secret_hash is None:
            raise jwt.InvalidTokenError()
        claims = validar_token_m2m(token, settings)
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token do laboratório inválido ou ausente.",
                            headers={"WWW-Authenticate": "Bearer"}) from None
    return claims


def laboratorio(security_scopes: SecurityScopes, request: Request,
                _authorization: Annotated[str | None, Depends(client_bearer)]) -> dict:
    claims = getattr(request.state, "laboratorio", None)
    if claims is None:
        raise HTTPException(401, "Token do laboratório inválido ou ausente.",
                            headers={"WWW-Authenticate": "Bearer"})
    concedidos = set(claims["scope"].split())
    if concedidos - {DISPONIBILIDADE_SCOPE} or not set(security_scopes.scopes).issubset(concedidos):
        raise HTTPException(403, "Escopo insuficiente ou não permitido.",
            headers={"WWW-Authenticate": f'Bearer error="insufficient_scope", scope="{DISPONIBILIDADE_SCOPE}"'})
    return claims

LaboratorioDep = Annotated[dict, Security(laboratorio, scopes=[DISPONIBILIDADE_SCOPE])]
