"""Disponibilidade calculada na agenda de demonstração aprovada."""
from datetime import date, datetime, time, timedelta
from app.database.consultas import FUSO_CLINICA, horario_na_clinica, listar_consultas
from app.models.disponibilidade import IntervaloLivre

DURACAO_CONSULTA = timedelta(minutes=30)
INICIO_EXPEDIENTE = time(8)
FIM_EXPEDIENTE = time(18)


def intervalos_livres(dia: date, profissional_id: int) -> list[IntervaloLivre]:
    if dia.weekday() >= 5:
        return []
    ocupados = [
        (horario_na_clinica(consulta.data_hora), horario_na_clinica(consulta.data_hora) + DURACAO_CONSULTA)
        for consulta in listar_consultas(profissional_id=profissional_id)
        if consulta.status != "cancelada"
    ]
    inicio = datetime.combine(dia, INICIO_EXPEDIENTE, tzinfo=FUSO_CLINICA)
    encerramento = datetime.combine(dia, FIM_EXPEDIENTE, tzinfo=FUSO_CLINICA)
    livres = []
    while inicio + DURACAO_CONSULTA <= encerramento:
        fim = inicio + DURACAO_CONSULTA
        if not any(inicio < ocupado_fim and fim > ocupado_inicio for ocupado_inicio, ocupado_fim in ocupados):
            livres.append(IntervaloLivre(inicio=inicio, fim=fim))
        inicio = fim
    return livres
