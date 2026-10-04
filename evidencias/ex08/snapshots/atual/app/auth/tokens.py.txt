"""JWT com contratos e audiências distintos para usuários e laboratório."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from app.models.identidades import Usuario
from app.settings import Settings

BASE_REQUIRED = ["sub", "exp", "iat", "nbf", "iss", "aud", "jti", "token_use"]
M2M_AUDIENCE = "clinic-laboratory"
DISPONIBILIDADE_SCOPE = "disponibilidade:ler"


def claims_base(subject: str, audience: str, minutes: int, settings: Settings) -> dict:
    now = datetime.now(timezone.utc)
    return {"sub": subject, "iat": now, "nbf": now,
            "exp": now + timedelta(minutes=minutes), "iss": settings.jwt_issuer,
            "aud": audience, "jti": str(uuid4())}


def emitir_token(usuario: Usuario, settings: Settings, *, mfa: bool = False) -> str:
    claims = claims_base(usuario.username, settings.jwt_audience, settings.access_token_minutes, settings)
    claims.update(token_use="human_access", amr=["pwd", "mfa"] if mfa else ["pwd"])
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def validar_assinatura(token: str, settings: Settings, audience: str, extra: list[str]) -> dict:
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"], issuer=settings.jwt_issuer,
        audience=audience, options={"require": BASE_REQUIRED + extra})
    if any(type(claims[name]) is not int for name in ("exp", "iat", "nbf")):
        raise jwt.InvalidTokenError("Instantes devem ser inteiros NumericDate.")
    if not isinstance(claims["sub"], str) or not claims["sub"] or not isinstance(claims["jti"], str) or not claims["jti"]:
        raise jwt.InvalidTokenError("Identificadores obrigatórios inválidos.")
    if claims["aud"] != audience:
        raise jwt.InvalidTokenError("Audiência deve ser exclusiva da finalidade.")
    return claims


def validar_token(token: str, settings: Settings) -> dict:
    claims = validar_assinatura(token, settings, settings.jwt_audience, ["amr"])
    if claims["token_use"] != "human_access" or claims["amr"] not in (["pwd"], ["pwd", "mfa"]):
        raise jwt.InvalidTokenError("Finalidade ou métodos de autenticação inválidos.")
    return claims


def emitir_token_m2m(settings: Settings, scope: str) -> str:
    claims = claims_base("client:" + settings.m2m_client_id, M2M_AUDIENCE, settings.m2m_token_minutes, settings)
    claims.update(token_use="m2m_access", client_id=settings.m2m_client_id, scope=scope)
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def validar_token_m2m(token: str, settings: Settings) -> dict:
    claims = validar_assinatura(token, settings, M2M_AUDIENCE, ["client_id", "scope"])
    if (claims["token_use"] != "m2m_access" or claims["client_id"] != settings.m2m_client_id
            or claims["sub"] != "client:" + settings.m2m_client_id or not isinstance(claims["scope"], str)):
        raise jwt.InvalidTokenError("Identidade ou finalidade do cliente inválida.")
    return claims
