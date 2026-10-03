"""Operações de dados para o recurso de Consultas Médicas."""

from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from app.database import memoria
from app.database.memoria import _consultas, _lock
from app.models.consultas import Consulta, ConsultaCreate, ConsultaUpdate

FUSO_CLINICA = ZoneInfo("America/Sao_Paulo")


def horario_na_clinica(horario: datetime) -> datetime:
    """Horários sem fuso são locais; instantes com fuso são convertidos."""
    if horario.tzinfo is None:
        return horario.replace(tzinfo=FUSO_CLINICA)
    return horario.astimezone(FUSO_CLINICA)


def listar_consultas_do_dia(dia: date) -> List[Consulta]:
    """Reutiliza a leitura em memória e ordena a agenda pelo instante local."""
    consultas = [
        consulta for consulta in listar_consultas()
        if horario_na_clinica(consulta.data_hora).date() == dia
    ]
    return sorted(consultas, key=lambda consulta: horario_na_clinica(consulta.data_hora))


def criar_consulta(dados: ConsultaCreate) -> Consulta:
    """Cria e armazena uma nova consulta em memória."""
    with _lock:
        memoria._contador_consultas += 1
        novo_id = memoria._contador_consultas
        agora = datetime.now()
        
        registro = {
            "id": novo_id,
            "paciente_id": dados.paciente_id,
            "profissional_id": dados.profissional_id,
            "data_hora": dados.data_hora,
            "motivo": dados.motivo,
            "status": "agendada",
            "observacoes_internas": dados.observacoes_internas,
            "criado_em": agora,
            "atualizado_em": agora,
        }
        _consultas[novo_id] = registro
        return Consulta(**registro)


def listar_consultas(
    paciente_id: Optional[int] = None,
    profissional_id: Optional[int] = None
) -> List[Consulta]:
    """Retorna lista de consultas cadastradas, com filtros opcionais."""
    with _lock:
        resultados = []
        for registro in _consultas.values():
            if paciente_id is not None and registro["paciente_id"] != paciente_id:
                continue
            if profissional_id is not None and registro["profissional_id"] != profissional_id:
                continue
            resultados.append(Consulta(**registro))
        return resultados


def obter_consulta_por_id(consulta_id: int) -> Optional[Consulta]:
    """Retorna uma consulta pelo ID ou None se não existir."""
    with _lock:
        registro = _consultas.get(consulta_id)
        if registro:
            return Consulta(**registro)
        return None


def atualizar_consulta(consulta_id: int, dados: ConsultaUpdate) -> Optional[Consulta]:
    """Atualiza campos de uma consulta existente."""
    with _lock:
        registro = _consultas.get(consulta_id)
        if not registro:
            return None
        
        dados_atualizacao = dados.model_dump(exclude_unset=True)
        if dados_atualizacao:
            registro.update(dados_atualizacao)
            registro["atualizado_em"] = datetime.now()
            _consultas[consulta_id] = registro
            
        return Consulta(**registro)


def remover_consulta(consulta_id: int) -> bool:
    """Remove uma consulta do armazenamento. Retorna True se removida, False se não encontrada."""
    with _lock:
        if consulta_id in _consultas:
            del _consultas[consulta_id]
            return True
        return False
