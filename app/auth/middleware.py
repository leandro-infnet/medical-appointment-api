"""Validação JWT na fronteira HTTP; autorização de recursos permanece nas políticas."""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

from app.auth.dependencies import identidade
from app.auth.m2m import identidade_laboratorio
from app.settings import get_settings


def autenticar_request(request: Request, maquina: bool) -> None:
    settings = get_settings()
    authorization = request.headers.get("Authorization")
    if maquina:
        request.state.laboratorio = identidade_laboratorio(authorization, settings)
        return
    scheme, _, token = (authorization or "").partition(" ")
    # Cookie somente na agenda; cabeçalho inválido não cai para cookie válido.
    credential = token if scheme.lower() == "bearer" else None
    if authorization is None and request.url.path.rstrip("/") == "/agenda":
        credential = request.cookies.get("agenda_session")
    request.state.usuario = identidade(credential, settings, request.app.state.usuarios)


class JWTMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        path = request.url.path
        humano = any(path == prefix or path.startswith(prefix + "/")
                     for prefix in ("/consultas", "/agenda", "/admin", "/auth/agenda-session"))
        maquina = path == "/disponibilidade" or path.startswith("/disponibilidade/")
        if humano or maquina:
            try:
                autenticar_request(request, maquina)
            except HTTPException as error:
                response = JSONResponse({"detail": error.detail}, status_code=error.status_code,
                                        headers={**(error.headers or {}), "Cache-Control": "no-store"})
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
