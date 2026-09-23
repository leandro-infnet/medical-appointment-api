"""Ponto de entrada e composição da aplicação FastAPI."""

from fastapi import FastAPI
from app.routes.consultas import router as consultas_router

app = FastAPI(
    title="API de Agendamento de Consultas Médicas",
    version="0.1.0",
    description="API RESTful segura para agendamento de consultas em clínicas médicas.",
)

app.include_router(consultas_router)


@app.get("/", tags=["Saúde"])
def root():
    """Endpoint raiz para verificação de status do serviço."""
    return {
        "status": "online",
        "servico": "API de Agendamento de Consultas Médicas",
        "versao": "0.1.0",
    }
