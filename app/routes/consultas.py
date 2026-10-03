"""Roteador APIRouter para o recurso RESTful de Consultas."""

from typing import Annotated, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.database.consultas import (
    criar_consulta,
    listar_consultas,
    obter_consulta_por_id,
    atualizar_consulta,
    remover_consulta,
)
from app.models.consultas import Consulta, ConsultaCreate, ConsultaUpdate

router = APIRouter(prefix="/consultas", tags=["Consultas"])


@router.post(
    "",
    response_model=Consulta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar uma nova consulta médica",
    description="Registra uma nova consulta vinculando paciente e profissional de saúde.",
)
def endpoint_criar_consulta(dados: ConsultaCreate):
    return criar_consulta(dados)


@router.get(
    "",
    response_model=List[Consulta],
    status_code=status.HTTP_200_OK,
    summary="Listar consultas médicas",
    description="Retorna a lista de consultas cadastradas com filtros opcionais.",
)
def endpoint_listar_consultas(
    paciente_id: Annotated[
        Optional[int], Query(description="Filtrar por ID do paciente", gt=0)
    ] = None,
    profissional_id: Annotated[
        Optional[int], Query(description="Filtrar por ID do profissional", gt=0)
    ] = None,
):
    return listar_consultas(paciente_id=paciente_id, profissional_id=profissional_id)


@router.get(
    "/{consulta_id}",
    response_model=Consulta,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma consulta",
    description="Retorna os dados de uma consulta específica a partir de seu ID.",
)
def endpoint_obter_consulta(consulta_id: int):
    consulta = obter_consulta_por_id(consulta_id)
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID {consulta_id} não encontrada."
        )
    return consulta


@router.patch(
    "/{consulta_id}",
    response_model=Consulta,
    status_code=status.HTTP_200_OK,
    summary="Atualizar uma consulta médica",
    description="Atualiza parcialmente campos permitidos de uma consulta existente.",
)
def endpoint_atualizar_consulta(consulta_id: int, dados: ConsultaUpdate):
    consulta = atualizar_consulta(consulta_id, dados)
    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID {consulta_id} não encontrada."
        )
    return consulta


@router.delete(
    "/{consulta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover/cancelar uma consulta",
    description="Remove a consulta médica pelo seu ID.",
)
def endpoint_remover_consulta(consulta_id: int):
    removido = remover_consulta(consulta_id)
    if not removido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID {consulta_id} não encontrada."
        )
    return None
