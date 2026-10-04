"""Leitura exclusiva do laboratório, sem consultas ou informações clínicas."""
from datetime import date
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Response
from app.auth.m2m import LaboratorioDep
from app.database.disponibilidade import intervalos_livres
from app.database.memoria import PROFISSIONAIS_SEEDS
from app.database.consultas import FUSO_CLINICA
from app.models.disponibilidade import DisponibilidadeResponse

router = APIRouter(tags=["Laboratório"])

@router.get("/disponibilidade", response_model=DisponibilidadeResponse,
    responses={401: {"description": "Token de cliente inválido ou ausente."},
               403: {"description": "Escopo insuficiente."},
               404: {"description": "Profissional não cadastrado."}})
def disponibilidade(laboratorio: LaboratorioDep, response: Response,
                    dia: Annotated[date, Query(description="Dia local da clínica")],
                    profissional_id: Annotated[int, Query(gt=0)]):
    if profissional_id not in PROFISSIONAIS_SEEDS:
        raise HTTPException(404, "Profissional não cadastrado.")
    response.headers["Cache-Control"] = "no-store"
    return DisponibilidadeResponse(profissional_id=profissional_id, dia=dia,
        fuso=FUSO_CLINICA.key, intervalos=intervalos_livres(dia, profissional_id))
