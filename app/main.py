"""Ponto de entrada e composição da aplicação FastAPI."""

from contextlib import asynccontextmanager
from secrets import token_urlsafe
from fastapi import FastAPI
from app.auth.mfa import MFAStore
from app.auth.passwords import gerar_hash
from app.database.identidades import carregar_usuarios
from app.settings import get_settings
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    application.state.usuarios = carregar_usuarios(settings.users_file)
    application.state.dummy_hash = gerar_hash(token_urlsafe(24))
    application.state.mfa = MFAStore()
    yield

from app.routes.consultas import router as consultas_router
from app.routes.agenda import router as agenda_router

app = FastAPI(
    lifespan=lifespan,
    title="API de Agendamento de Consultas Médicas",
    version="0.1.0",
    description="API RESTful segura para agendamento de consultas em clínicas médicas.",
)

app.include_router(consultas_router)
app.include_router(agenda_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/", tags=["Saúde"])
def root():
    """Endpoint raiz para verificação de status do serviço."""
    return {
        "status": "online",
        "servico": "API de Agendamento de Consultas Médicas",
        "versao": "0.1.0",
    }
