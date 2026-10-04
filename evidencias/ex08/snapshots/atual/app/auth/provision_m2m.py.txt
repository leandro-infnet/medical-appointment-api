"""Gera hash para credencial fictícia do parceiro, sem alterar o .env existente."""
from getpass import getpass
from app.auth.passwords import gerar_hash


def main():
    secret = getpass("Segredo fictício do laboratório (8–72 bytes UTF-8): ")
    if secret != getpass("Confirme o segredo: "):
        raise SystemExit("Confirmação diferente; nenhum hash gerado.")
    print("Copie somente para M2M_CLIENT_SECRET_HASH no .env local; não salve em evidências:")
    print(gerar_hash(secret))

if __name__ == "__main__":
    main()
