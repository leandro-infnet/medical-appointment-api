"""Modelos Pydantic para o recurso de Consultas Médicas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ConsultaBase(BaseModel):
    paciente_id: int = Field(..., description="ID do paciente associado à consulta", gt=0)
    profissional_id: int = Field(..., description="ID do profissional de saúde responsável", gt=0)
    data_hora: datetime = Field(..., description="Data e horário agendados para a consulta")
    motivo: str = Field(..., min_length=3, max_length=255, description="Motivo ou especialidade da consulta")


class ConsultaCreate(ConsultaBase):
    observacoes_internas: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas de auditoria ou observações internas da equipe médica"
    )


class ConsultaUpdate(BaseModel):
    data_hora: Optional[datetime] = Field(None, description="Nova data e horário")
    status: Optional[str] = Field(None, description="Novo status da consulta (ex: agendada, cancelada, realizada)")
    motivo: Optional[str] = Field(None, min_length=3, max_length=255, description="Novo motivo")
    observacoes_internas: Optional[str] = Field(None, max_length=500, description="Atualização das notas internas")

    @field_validator("data_hora", "status", "motivo")
    @classmethod
    def impedir_nulo_em_campos_obrigatorios(cls, valor):
        if valor is None:
            raise ValueError("O campo não pode ser nulo.")
        return valor


class ConsultaResponse(ConsultaBase):
    """Contrato JSON: somente campos destinados ao consumidor da API."""

    id: int = Field(..., description="Identificador único da consulta")
    status: str = Field(..., description="Estado atual da consulta")


class Consulta(ConsultaBase):
    id: int = Field(..., description="Identificador único da consulta")
    status: str = Field(default="agendada", description="Estado atual da consulta")
    observacoes_internas: Optional[str] = Field(None, description="Notas de auditoria ou observações internas")
    criado_em: datetime = Field(default_factory=datetime.now, description="Data/hora de registro")
    atualizado_em: datetime = Field(default_factory=datetime.now, description="Data/hora da última atualização")
