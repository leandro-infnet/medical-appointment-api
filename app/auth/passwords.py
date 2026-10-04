"""Hash bcrypt sem truncamento silencioso de senhas UTF-8."""
import bcrypt

def gerar_hash(senha: str, *, rounds: int = 12) -> str:
    raw = senha.encode("utf-8")
    if not 8 <= len(raw) <= 72:
        raise ValueError("A senha deve ter entre 8 e 72 bytes UTF-8.")
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=rounds)).decode("ascii")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    raw = senha.encode("utf-8")
    if not 8 <= len(raw) <= 72:
        return False
    return bcrypt.checkpw(raw, senha_hash.encode("ascii"))
