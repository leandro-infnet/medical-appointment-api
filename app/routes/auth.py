"""Login humano, conclusão de MFA e sessão de leitura da agenda."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestFormStrict
from app.auth.dependencies import SettingsDep, UsuariosDep, UsuarioDep
from app.auth.passwords import verificar_senha
from app.auth.policies import exigir_papel
from app.auth.tokens import emitir_token
from app.settings import Settings
from app.models.identidades import MFAChallengeResponse, MFAInput, Papel, TokenResponse, Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

def resposta_token(usuario: Usuario, settings: Settings, *, mfa: bool = False) -> TokenResponse:
    return TokenResponse(access_token=emitir_token(usuario, settings, mfa=mfa),
                         expires_in=settings.access_token_minutes * 60)

@router.post("/token", response_model=TokenResponse | MFAChallengeResponse,
             responses={202: {"model": MFAChallengeResponse}, 401: {"description": "Credenciais inválidas"}})
def login(form: Annotated[OAuth2PasswordRequestFormStrict, Depends()], request: Request,
          response: Response, settings: SettingsDep, cadastro: UsuariosDep):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    usuario = cadastro.get(form.username)
    # A verificação ocorre também para nomes inexistentes, usando hash fictício.
    senha_hash = usuario.senha_hash.get_secret_value() if usuario else request.app.state.dummy_hash
    senha_valida = verificar_senha(form.password, senha_hash)
    if usuario is None or not usuario.ativo or not senha_valida:
        raise HTTPException(401, "Credenciais inválidas.", headers={"WWW-Authenticate": "Bearer"})
    if usuario.papel == Papel.ADMIN:
        response.status_code = 202
        return MFAChallengeResponse(challenge_id=request.app.state.mfa.criar(usuario.username))
    return resposta_token(usuario, settings)

@router.post(
    "/mfa", response_model=TokenResponse,
    responses={401: {"description": "Desafio inválido, expirado ou código incorreto."}},
)
def completar_mfa(dados: MFAInput, request: Request, response: Response,
                  settings: SettingsDep, cadastro: UsuariosDep):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    username = request.app.state.mfa.concluir(dados.challenge_id,
        dados.code.get_secret_value(), settings.mfa_simulated_code.get_secret_value())
    usuario = cadastro.get(username) if username else None
    if usuario is None or not usuario.ativo or usuario.papel != Papel.ADMIN:
        raise HTTPException(401, "Desafio inválido, expirado ou código incorreto.")
    return resposta_token(usuario, settings, mfa=True)

@router.post("/agenda-session", status_code=204)
def criar_sessao_agenda(usuario: UsuarioDep, settings: SettingsDep, response: Response):
    exigir_papel(usuario, Papel.RECEPCAO)
    response.set_cookie("agenda_session", emitir_token(usuario, settings),
        httponly=True, secure=settings.agenda_cookie_secure, samesite="strict",
        path="/agenda", max_age=settings.access_token_minutes * 60)
    response.headers["Cache-Control"] = "no-store"

@router.delete("/agenda-session", status_code=204)
def encerrar_sessao_agenda(usuario: UsuarioDep, settings: SettingsDep, response: Response):
    exigir_papel(usuario, Papel.RECEPCAO)
    response.delete_cookie("agenda_session", path="/agenda",
        secure=settings.agenda_cookie_secure, httponly=True, samesite="strict")
