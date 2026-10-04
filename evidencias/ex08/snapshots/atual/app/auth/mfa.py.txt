"""Desafios de uso único em memória para demonstração de segundo fator."""
from dataclasses import dataclass
from secrets import compare_digest, token_urlsafe
from threading import Lock
from time import monotonic

@dataclass
class Desafio:
    username: str
    expires_at: float
    tentativas: int = 0

class MFAStore:
    def __init__(self):
        self._desafios: dict[str, Desafio] = {}
        self._lock = Lock()

    def criar(self, username: str) -> str:
        with self._lock:
            now = monotonic()
            self._desafios = {k: v for k, v in self._desafios.items() if v.expires_at > now}
            # Um desafio vigente por conta limita crescimento de estado por conta.
            self._desafios = {k: v for k, v in self._desafios.items() if v.username != username}
            challenge = token_urlsafe(32)
            self._desafios[challenge] = Desafio(username, now + 300)
            return challenge

    def concluir(self, challenge: str, code: str, expected: str) -> str | None:
        with self._lock:
            item = self._desafios.get(challenge)
            if item is None:
                return None
            item.tentativas += 1
            valido = item.expires_at > monotonic() and compare_digest(code.encode(), expected.encode())
            if valido or item.tentativas >= 5 or item.expires_at <= monotonic():
                del self._desafios[challenge]
            return item.username if valido else None
