"""Roteador APIRouter para o recurso RESTful de Consultas."""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.database.session import SessionDep
from app.database.consultas import (
    criar_consulta,
    listar_consultas,
    atualizar_consulta,
    remover_consulta,
)
from app.auth.policies import profissional, pode_acessar, exigir_vinculo, consulta_autorizada
from app.models.identidades import Usuario

from app.models.consultas import ConsultaResponse, ConsultaCreate, ConsultaUpdate

ProfissionalDep = Annotated[Usuario, Depends(profissional)]

router = APIRouter(
    prefix="/consultas", tags=["Consultas"],
    responses={
        401: {"description": "Autenticação necessária ou inválida."},
        403: {"description": "Papel ou vínculo não autorizado."},
        503: {"description": "Banco temporariamente ocupado."},
    },
)


@router.post(
    "",
    response_model=ConsultaResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Intervalo já ocupado pelo profissional."}},
    summary="Criar uma nova consulta médica",
    description="Registra uma nova consulta vinculando paciente e profissional de saúde.",
)
def endpoint_criar_consulta(dados: ConsultaCreate, usuario: ProfissionalDep, session: SessionDep):
    exigir_vinculo(usuario, dados.paciente_id, dados.profissional_id)
    return criar_consulta(session, dados)


@router.get(
    "",
    response_model=List[ConsultaResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar consultas médicas",
    description="Retorna a lista de consultas cadastradas com filtros opcionais.",
)
def endpoint_listar_consultas(
    usuario: ProfissionalDep,
    session: SessionDep,
    paciente_id: Annotated[
        Optional[int], Query(description="Filtrar por ID do paciente", gt=0)
    ] = None,
    profissional_id: Annotated[
        Optional[int], Query(description="Filtrar por ID do profissional", gt=0)
    ] = None,
):
    if profissional_id is not None and profissional_id != usuario.profissional_id:
        return []
    return [consulta for consulta in listar_consultas(session,
        paciente_id=paciente_id, profissional_id=usuario.profissional_id)
        if pode_acessar(usuario, consulta.paciente_id, consulta.profissional_id)]


@router.get(
    "/{consulta_id}",
    responses={404: {"description": "Consulta inexistente ou não autorizada."}},
    response_model=ConsultaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma consulta",
    description="Retorna os dados de uma consulta específica a partir de seu ID.",
)
def endpoint_obter_consulta(consulta_id: int, usuario: ProfissionalDep, session: SessionDep):
    return consulta_autorizada(consulta_id, usuario, session)


@router.patch(
    "/{consulta_id}",
    responses={404: {"description": "Consulta inexistente ou não autorizada."},
               409: {"description": "Intervalo já ocupado pelo profissional."}},
    response_model=ConsultaResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar uma consulta médica",
    description="Atualiza parcialmente campos permitidos de uma consulta existente.",
)
def endpoint_atualizar_consulta(consulta_id: int, dados: ConsultaUpdate, usuario: ProfissionalDep, session: SessionDep):
    consulta_autorizada(consulta_id, usuario, session)
    return atualizar_consulta(session, consulta_id, dados)


@router.delete(
    "/{consulta_id}",
    responses={404: {"description": "Consulta inexistente ou não autorizada."}},
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover/cancelar uma consulta",
    description="Remove a consulta médica pelo seu ID.",
)
def endpoint_remover_consulta(consulta_id: int, usuario: ProfissionalDep, session: SessionDep):
    consulta_autorizada(consulta_id, usuario, session)
    remover_consulta(session, consulta_id)
    return None
