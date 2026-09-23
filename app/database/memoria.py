"""Armazenamento temporário em memória para a fase inicial do Assessment."""

from threading import Lock
from typing import Dict, Any

_lock = Lock()

_consultas: Dict[int, Dict[str, Any]] = {}
_contador_consultas: int = 0

PACIENTES_SEEDS = {
    1: {"id": 1, "nome": "Douglas Heffernan", "email": "douglas@sitcom.com"},
    2: {"id": 2, "nome": "Arthur Spooner", "email": "arthur@sitcom.com"},
}

PROFISSIONAIS_SEEDS = {
    1: {"id": 1, "nome": "Dr. Carrie Heffernan", "especialidade": "Cardiologia", "crm": "12345-SP"},
    2: {"id": 2, "nome": "Dr. Kelly Palmer", "especialidade": "Ortopedia", "crm": "67890-SP"},
}


def reset_banco() -> None:
    """Reseta o estado do banco em memória para isolamento de testes."""
    global _contador_consultas
    with _lock:
        _consultas.clear()
        _contador_consultas = 0
