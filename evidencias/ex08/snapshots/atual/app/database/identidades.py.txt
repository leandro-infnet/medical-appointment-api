"""Cadastro local confiável; sem endpoint de alteração de papéis ou vínculos."""
import json
from pathlib import Path
from pydantic import TypeAdapter
from app.models.identidades import Usuario

VINCULOS = frozenset({(1, 1), (2, 1), (2, 2)})

def carregar_usuarios(path: Path) -> dict[str, Usuario]:
    usuarios = TypeAdapter(list[Usuario]).validate_python(json.loads(path.read_text()))
    cadastro = {usuario.username: usuario for usuario in usuarios}
    if len(cadastro) != len(usuarios):
        raise ValueError("Cadastro contém usernames duplicados.")
    return cadastro
