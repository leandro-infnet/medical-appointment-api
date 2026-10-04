"""Leitura exclusiva do laboratório, sem consultas ou informações clínicas."""
from datetime import date
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Response
from app.auth.m2m import LaboratorioDep
from app.database.disponibilidade import intervalos_livres
from app.database.session import SessionDep
from app.models.tabelas import ProfissionalTabela
from app.database.consultas import FUSO_CLINICA
from app.models.disponibilidade import DisponibilidadeResponse

router = APIRouter(tags=["Laboratório"])

@router.get("/disponibilidade", response_model=DisponibilidadeResponse,
    responses={401: {"description": "Token de cliente inválido ou ausente."},
               403: {"description": "Escopo insuficiente."},
               404: {"description": "Profissional não cadastrado."}})
def disponibilidade(laboratorio: LaboratorioDep, response: Response, session: SessionDep,
                    dia: Annotated[date, Query(description="Dia local da clínica")],
                    profissional_id: Annotated[int, Query(gt=0)]):
    if session.get(ProfissionalTabela, profissional_id) is None:
        raise HTTPException(404, "Profissional não cadastrado.")
    response.headers["Cache-Control"] = "no-store"
    return DisponibilidadeResponse(profissional_id=profissional_id, dia=dia,
        fuso=FUSO_CLINICA.key, intervalos=intervalos_livres(session, dia, profissional_id))
