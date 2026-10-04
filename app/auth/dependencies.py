"""Um validador de identidade para bearer JSON e cookie exclusivo da agenda."""
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from app.auth.tokens import validar_token
from app.models.identidades import Papel, Usuario
from app.settings import Settings, get_settings

bearer = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
SettingsDep = Annotated[Settings, Depends(get_settings)]

def usuarios(request: Request) -> dict[str, Usuario]:
    return request.app.state.usuarios

UsuariosDep = Annotated[dict[str, Usuario], Depends(usuarios)]

def identidade(token: str | None, settings: Settings, cadastro: dict[str, Usuario]) -> Usuario:
    try:
        if not token:
            raise jwt.InvalidTokenError()
        claims = validar_token(token, settings)
        usuario = cadastro.get(claims["sub"])
        if usuario is None or not usuario.ativo:
            raise jwt.InvalidTokenError()
        if usuario.papel == Papel.ADMIN and "mfa" not in claims["amr"]:
            raise jwt.InvalidTokenError()
        return usuario
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Autenticação necessária ou inválida.",
            headers={"WWW-Authenticate": "Bearer"}) from None

def usuario_atual(request: Request, _token: Annotated[str | None, Depends(bearer)]) -> Usuario:
    usuario = getattr(request.state, "usuario", None)
    if usuario is None:
        raise HTTPException(401, "Autenticação necessária ou inválida.",
                            headers={"WWW-Authenticate": "Bearer"})
    return usuario

UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]

AgendaDep = UsuarioDep
