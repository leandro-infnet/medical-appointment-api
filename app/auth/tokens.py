"""Emissão e validação centralizadas de tokens humanos assinados."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from app.models.identidades import Usuario
from app.settings import Settings

REQUIRED = ["sub", "exp", "iat", "nbf", "iss", "aud", "jti", "token_use", "amr"]

def emitir_token(usuario: Usuario, settings: Settings, *, mfa: bool = False) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": usuario.username, "iat": now, "nbf": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
        "jti": str(uuid4()), "token_use": "human_access",
        "amr": ["pwd", "mfa"] if mfa else ["pwd"],
    }, settings.jwt_secret.get_secret_value(), algorithm="HS256")

def validar_token(token: str, settings: Settings) -> dict:
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"], issuer=settings.jwt_issuer,
        audience=settings.jwt_audience, options={"require": REQUIRED})
    if any(type(claims[name]) is not int for name in ("exp", "iat", "nbf")):
        raise jwt.InvalidTokenError("Instantes devem ser inteiros NumericDate.")
    if not isinstance(claims["sub"], str) or not claims["sub"] or not isinstance(claims["jti"], str) or not claims["jti"]:
        raise jwt.InvalidTokenError("Identificadores obrigatórios inválidos.")
    if claims["token_use"] != "human_access" or claims["amr"] not in (["pwd"], ["pwd", "mfa"]):
        raise jwt.InvalidTokenError("Finalidade ou métodos de autenticação inválidos.")
    return claims
