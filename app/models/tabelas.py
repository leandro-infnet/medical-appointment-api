"""Tabelas relacionais internas; os contratos HTTP continuam em consultas.py."""
from datetime import datetime, timezone
from typing import ClassVar
from sqlalchemy import CheckConstraint, DateTime
from sqlmodel import Field, SQLModel


def agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PacienteTabela(SQLModel, table=True):
    __tablename__: ClassVar[str] = "pacientes"
    id: int = Field(primary_key=True)
    nome: str
    email: str


class ProfissionalTabela(SQLModel, table=True):
    __tablename__: ClassVar[str] = "profissionais"
    id: int = Field(primary_key=True)
    nome: str
    especialidade: str
    crm: str


class ConsultaTabela(SQLModel, table=True):
    __tablename__: ClassVar[str] = "consultas"
    __table_args__ = (
        CheckConstraint("status IN ('agendada', 'cancelada', 'realizada')", name="consulta_status"),
        CheckConstraint("length(motivo) BETWEEN 3 AND 255", name="consulta_motivo"),
        CheckConstraint("observacoes_internas IS NULL OR length(observacoes_internas) <= 500",
                        name="consulta_observacoes"),
    )
    id: int | None = Field(default=None, primary_key=True)
    paciente_id: int = Field(foreign_key="pacientes.id", index=True)
    profissional_id: int = Field(foreign_key="profissionais.id", index=True)
    data_hora: datetime = Field(index=True, sa_type=DateTime)  # UTC sem offset no SQLite.
    motivo: str
    status: str = "agendada"
    observacoes_internas: str | None = None
    criado_em: datetime = Field(default_factory=agora_utc, sa_type=DateTime)
    atualizado_em: datetime = Field(default_factory=agora_utc, sa_type=DateTime)
