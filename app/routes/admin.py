"""Diagnóstico restrito, sem dados clínicos ou segredos."""
from fastapi import APIRouter
from app.auth.dependencies import UsuarioDep
from app.auth.policies import exigir_papel
from app.models.identidades import Papel

router = APIRouter(prefix="/admin", tags=["Administração"])

@router.get("/status", response_model=dict[str, str])
def status_administrativo(usuario: UsuarioDep):
    exigir_papel(usuario, Papel.ADMIN)
    return {"status": "online", "servico": "medical-appointment-api"}
