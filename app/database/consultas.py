"""CRUD SQLModel com parâmetros vinculados e transação da requisição."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlmodel import Session, col, select
from app.models.consultas import Consulta, ConsultaCreate, ConsultaUpdate
from app.models.tabelas import ConsultaTabela, agora_utc

FUSO_CLINICA = ZoneInfo("America/Sao_Paulo")
DURACAO_CONSULTA = timedelta(minutes=30)


class ConflitoAgenda(Exception):
    """Intervalo já ocupado pelo mesmo profissional."""


def horario_na_clinica(horario: datetime) -> datetime:
    if horario.tzinfo is None:
        return horario.replace(tzinfo=FUSO_CLINICA)
    return horario.astimezone(FUSO_CLINICA)


def horario_utc(horario: datetime) -> datetime:
    return horario_na_clinica(horario).astimezone(timezone.utc).replace(tzinfo=None)


def para_consulta(registro: ConsultaTabela) -> Consulta:
    dados = registro.model_dump()
    dados["data_hora"] = registro.data_hora.replace(tzinfo=timezone.utc).astimezone(FUSO_CLINICA)
    return Consulta.model_validate(dados)


def listar_consultas(session: Session, paciente_id: int | None = None,
                     profissional_id: int | None = None) -> list[Consulta]:
    query = select(ConsultaTabela)
    if paciente_id is not None:
        query = query.where(ConsultaTabela.paciente_id == paciente_id)
    if profissional_id is not None:
        query = query.where(ConsultaTabela.profissional_id == profissional_id)
    return [para_consulta(row) for row in session.exec(query.order_by(col(ConsultaTabela.id))).all()]


def listar_consultas_do_dia(session: Session, dia: date) -> list[Consulta]:
    inicio = horario_utc(datetime.combine(dia, time.min))
    fim = horario_utc(datetime.combine(dia + timedelta(days=1), time.min))
    query = select(ConsultaTabela).where(ConsultaTabela.data_hora >= inicio,
        ConsultaTabela.data_hora < fim).order_by(col(ConsultaTabela.data_hora), col(ConsultaTabela.id))
    return [para_consulta(row) for row in session.exec(query).all()]


def obter_consulta_por_id(session: Session, consulta_id: int) -> Consulta | None:
    registro = session.get(ConsultaTabela, consulta_id)
    return para_consulta(registro) if registro is not None else None


def verificar_conflito(session: Session, registro: ConsultaTabela) -> None:
    if registro.status == "cancelada":
        return
    query = select(ConsultaTabela.id).where(
        ConsultaTabela.profissional_id == registro.profissional_id,
        ConsultaTabela.status != "cancelada",
        ConsultaTabela.data_hora > registro.data_hora - DURACAO_CONSULTA,
        ConsultaTabela.data_hora < registro.data_hora + DURACAO_CONSULTA,
    )
    if registro.id is not None:
        query = query.where(ConsultaTabela.id != registro.id)
    with session.no_autoflush:
        if session.exec(query.limit(1)).first() is not None:
            raise ConflitoAgenda()


def criar_consulta(session: Session, dados: ConsultaCreate) -> Consulta:
    registro = ConsultaTabela(**{**dados.model_dump(), "data_hora": horario_utc(dados.data_hora)})
    verificar_conflito(session, registro)
    session.add(registro)
    session.commit()
    session.refresh(registro)
    return para_consulta(registro)


def atualizar_consulta(session: Session, consulta_id: int, dados: ConsultaUpdate) -> Consulta | None:
    registro = session.get(ConsultaTabela, consulta_id)
    if registro is None:
        return None
    valores = dados.model_dump(exclude_unset=True)
    if "data_hora" in valores:
        valores["data_hora"] = horario_utc(valores["data_hora"])
    if valores:
        registro.sqlmodel_update(valores)
        verificar_conflito(session, registro)
        registro.atualizado_em = agora_utc()
        session.add(registro)
        session.commit()
        session.refresh(registro)
    return para_consulta(registro)


def remover_consulta(session: Session, consulta_id: int) -> bool:
    registro = session.get(ConsultaTabela, consulta_id)
    if registro is None:
        return False
    session.delete(registro)
    session.commit()
    return True
