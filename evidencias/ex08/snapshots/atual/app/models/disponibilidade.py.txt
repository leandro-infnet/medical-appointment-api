"""Saída do parceiro contém apenas profissional e intervalos livres."""
from datetime import date, datetime
from pydantic import BaseModel

class IntervaloLivre(BaseModel):
    inicio: datetime
    fim: datetime

class DisponibilidadeResponse(BaseModel):
    profissional_id: int
    dia: date
    fuso: str
    intervalos: list[IntervaloLivre]
