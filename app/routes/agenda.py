"""Apresentação HTML da agenda, com projeção mínima para a recepção."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.auth.dependencies import AgendaDep
from app.auth.policies import exigir_papel
from app.models.identidades import Papel

from app.database.session import SessionDep
from app.database.consultas import (
    FUSO_CLINICA,
    horario_na_clinica,
    listar_consultas_do_dia,
)

router = APIRouter(tags=["Agenda"])
templates = Jinja2Templates(env=Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
    autoescape=select_autoescape(["html", "xml"], default_for_string=True),
))


@router.get("/agenda", response_class=HTMLResponse, summary="Consultar agenda diária")
def endpoint_agenda(
    request: Request,
    usuario: AgendaDep,
    session: SessionDep,
    dia: Annotated[date | None, Query(description="Dia local da clínica (AAAA-MM-DD)")] = None,
):
    exigir_papel(usuario, Papel.RECEPCAO)
    dia_agenda = dia if dia is not None else datetime.now(FUSO_CLINICA).date()
    # Não entregar a entidade completa ao template: escape não substitui minimização.
    consultas = [
        {
            "id": consulta.id,
            "paciente_id": consulta.paciente_id,
            "profissional_id": consulta.profissional_id,
            "horario": horario_na_clinica(consulta.data_hora).strftime("%H:%M"),
            "status": consulta.status,
        }
        for consulta in listar_consultas_do_dia(session, dia_agenda)
    ]
    response = templates.TemplateResponse(
        request=request,
        name="agenda.html",
        context={"dia": dia_agenda, "consultas": consultas},
    )

    response.headers["Cache-Control"] = "no-store"
    return response
