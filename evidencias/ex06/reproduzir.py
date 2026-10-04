"""Reprodução HTTP em processo com cadastro e segredos fictícios efêmeros."""
import json
import os
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fastapi.testclient import TestClient
from app.auth.passwords import gerar_hash
from app.database.memoria import reset_banco
from app.main import app
from app.settings import get_settings


CONSULTAS_PATH = "/consultas"
ADMIN_STATUS_PATH = "/admin/status"
MFA_PATH = "/auth/mfa"


def main():
    destino = Path(__file__).resolve().parent
    env_names = ["JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "AGENDA_COOKIE_SECURE"]
    anteriores = {name: os.environ.get(name) for name in env_names}
    resultados = []
    try:
        with TemporaryDirectory() as temp:
            cadastro = Path(temp) / "usuarios.json"
            senha = token_urlsafe(24)
            code = f"{int.from_bytes(os.urandom(4)) % 1000000:06d}"
            senha_hash = gerar_hash(senha)
            cadastro.write_text(json.dumps([
                {"username": name, "papel": role, "profissional_id": prof, "senha_hash": senha_hash}
                for name, role, prof in [("profissional1", "profissional", 1),
                    ("profissional2", "profissional", 2), ("recepcao", "recepcionista", None),
                    ("admin", "administrador", None)]
            ]))
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE=code,
                              USERS_FILE=str(cadastro), AGENDA_COOKIE_SECURE="false")
            get_settings.cache_clear()
            reset_banco()
            with TestClient(app) as client:
                def registrar(cenario, response, expected, *, segredo=False):
                    assert response.status_code == expected, cenario
                    if segredo:
                        body = "[conteúdo de autenticação omitido]"
                    elif response.content and response.headers.get("content-type", "").startswith("application/json"):
                        body = response.json()
                    else:
                        body = "[HTML/sem conteúdo]"
                    resultados.append({"cenario": cenario, "metodo": response.request.method,
                        "path": response.request.url.path, "status": response.status_code,
                        "body": body,
                        "cache_control": response.headers.get("cache-control")})
                def login(name):
                    return client.post("/auth/token", data={"grant_type": "password", "username": name, "password": senha})
                def headers(response):
                    return {"Authorization": "Bearer " + response.json()["access_token"]}
                registrar("Anônimo na API", client.get(CONSULTAS_PATH), 401)
                profissional = login("profissional1")
                registrar("Login profissional", profissional, 200, segredo=True)
                registrar("Não administrador na rota administrativa", client.get(ADMIN_STATUS_PATH, headers=headers(profissional)), 403)
                payload = {"paciente_id": 1, "profissional_id": 1,
                           "data_hora": "2026-10-15T10:00:00", "motivo": "Rotina fictícia"}
                criada = client.post(CONSULTAS_PATH, json=payload, headers=headers(profissional))
                registrar("Criação com vínculo autorizado", criada, 201)
                outro = login("profissional2")
                path = f"/consultas/{criada.json()['id']}"
                registrar("Outro profissional lê recurso", client.get(path, headers=headers(outro)), 404)
                registrar("Outro profissional altera recurso", client.patch(path, json={"motivo": "Tentativa fictícia"}, headers=headers(outro)), 404)
                registrar("Outro profissional remove recurso", client.delete(path, headers=headers(outro)), 404)
                registrar("Listagem não vaza recurso", client.get(CONSULTAS_PATH, headers=headers(outro)), 200)
                registrar("Criação sem vínculo", client.post(CONSULTAS_PATH, json={**payload, "profissional_id": 2}, headers=headers(outro)), 403)
                pendente = login("admin")
                registrar("Admin precisa de MFA; não recebe token", pendente, 202, segredo=True)
                challenge = pendente.json()["challenge_id"]
                registrar("Desafio não é bearer", client.get(ADMIN_STATUS_PATH, headers={"Authorization": "Bearer " + challenge}), 401)
                errado = "999999" if code != "999999" else "000000"
                registrar("Segundo fator incorreto", client.post(MFA_PATH, json={"challenge_id": challenge, "code": errado}), 401)
                completo = client.post(MFA_PATH, json={"challenge_id": challenge, "code": code})
                registrar("Segundo fator validado", completo, 200, segredo=True)
                registrar("Admin autenticado", client.get(ADMIN_STATUS_PATH, headers=headers(completo)), 200)
                registrar("Admin sem permissão clínica implícita", client.get(CONSULTAS_PATH, headers=headers(completo)), 403)
                registrar("Replay do desafio bloqueado", client.post(MFA_PATH, json={"challenge_id": challenge, "code": code}), 401)
                recepcao = login("recepcao")
                sessao = client.post("/auth/agenda-session", headers=headers(recepcao))
                registrar("Sessão de agenda criada", sessao, 204)
                resultados[-1]["cookie_flags"] = {"httponly": "HttpOnly" in sessao.headers["set-cookie"], "path": "/agenda", "samesite": "strict", "secure": False}
                agenda = client.get("/agenda?dia=2026-10-15")
                registrar("Agenda navegável via cookie", agenda, 200)
                (destino / "agenda_autenticada.html").write_text(
                    "\n".join(line.rstrip() for line in agenda.text.splitlines()) + "\n")
                registrar("Cookie não autentica API JSON", client.get(CONSULTAS_PATH), 401)
                registrar("Encerramento da sessão", client.delete("/auth/agenda-session", headers=headers(recepcao)), 204)
                registrar("Agenda exige novo login após logout", client.get("/agenda"), 401)
            (destino / "respostas_http.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + "\n")
            ambiente = {"python": platform.python_version(), "plataforma": platform.platform(),
                       "pacotes": {name: version(name) for name in ["fastapi", "bcrypt", "PyJWT", "pydantic-settings", "python-multipart", "pytest", "httpx"]}}
            (destino / "ambiente.json").write_text(json.dumps(ambiente, indent=2) + "\n")
            print(f"{len(resultados)} cenários HTTP verificados; segredos omitidos.")
    finally:
        for name, value in anteriores.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        get_settings.cache_clear()
        reset_banco()

if __name__ == "__main__":
    main()
