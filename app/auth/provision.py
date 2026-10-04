"""Provisionamento interativo de quatro contas fictícias para execução local."""
import json
import os
from getpass import getpass
from app.auth.passwords import gerar_hash
from app.settings import get_settings

def main():
    settings = get_settings()
    path = settings.users_file
    if path.exists():
        raise SystemExit("Cadastro já existe; não foi sobrescrito.")
    contas = []
    for username, papel, profissional_id in [
        ("profissional1", "profissional", 1), ("profissional2", "profissional", 2),
        ("recepcao", "recepcionista", None), ("admin", "administrador", None),
    ]:
        senha = getpass(f"Senha fictícia para {username} (8–72 bytes UTF-8): ")
        if senha != getpass("Confirme a senha: "):
            raise SystemExit("Confirmação diferente; cadastro não gravado.")
        contas.append({
            "username": username,
            "papel": papel,
            "profissional_id": profissional_id,
            "senha_hash": gerar_hash(senha),
            "ativo": True,
        })
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as arquivo:
        json.dump(contas, arquivo, indent=2)
    print("Cadastro fictício criado. Hashes e credenciais permanecem fora da entrega.")

if __name__ == "__main__":
    main()
