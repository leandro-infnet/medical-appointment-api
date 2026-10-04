"""Ponto de entrada e composição da aplicação FastAPI."""

from contextlib import asynccontextmanager
from secrets import token_urlsafe
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.errors import validation_error_response
from app.auth.mfa import MFAStore
from app.auth.m2m import OAuthClientError, oauth_error_response
from app.auth.middleware import JWTMiddleware
from app.auth.passwords import gerar_hash
from app.database.session import criar_engine, inicializar_banco, BancoIndisponivel
from app.database.consultas import ConflitoAgenda
from app.database.identidades import carregar_usuarios
from app.settings import get_settings
from app.network import NetworkMiddleware, RateLimiter
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.disponibilidade import router as disponibilidade_router
from app.routes.consultas import router as consultas_router
from app.routes.agenda import router as agenda_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    application.state.settings = settings
    application.state.rate_limiter = RateLimiter(settings.login_rate_limit, settings.general_rate_limit)
    application.state.usuarios = carregar_usuarios(settings.users_file)
    application.state.dummy_hash = gerar_hash(token_urlsafe(24))
    application.state.mfa = MFAStore()
    engine = criar_engine(settings.database_url.get_secret_value())
    application.state.engine = engine
    try:
        inicializar_banco(engine)
        yield
    finally:
        engine.dispose()

app = FastAPI(
    lifespan=lifespan,
    title="API de Agendamento de Consultas Médicas",
    version="0.1.0",
    description="API RESTful segura para agendamento de consultas em clínicas médicas.",
    responses={429: {"description": "Limite de requisições excedido.",
                     "headers": {"Retry-After": {"description": "Segundos até nova tentativa.",
                                                 "schema": {"type": "integer", "minimum": 1}}}}},
)

def conflito_agenda_response(_request, _error):
    return JSONResponse(status_code=409, content={"detail": "Horário indisponível para este profissional."})


def banco_indisponivel_response(_request, _error):
    return JSONResponse(status_code=503, content={"detail": "Banco temporariamente ocupado. Tente novamente."},
                        headers={"Retry-After": "5"})


app.add_exception_handler(ConflitoAgenda, conflito_agenda_response)
app.add_exception_handler(BancoIndisponivel, banco_indisponivel_response)
app.add_exception_handler(OAuthClientError, oauth_error_response)
app.add_exception_handler(RequestValidationError, validation_error_response)
app.add_middleware(JWTMiddleware)
app.add_middleware(NetworkMiddleware)

app.include_router(consultas_router)
app.include_router(agenda_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(disponibilidade_router)


@app.get("/", tags=["Saúde"])
def root():
    """Endpoint raiz para verificação de status do serviço."""
    return {
        "status": "online",
        "servico": "API de Agendamento de Consultas Médicas",
        "versao": "0.1.0",
    }
