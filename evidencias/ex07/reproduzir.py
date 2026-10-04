"""Evidências M2M em processo isolado, sem armazenar credenciais ou bearer."""
import json
import os
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import jwt
from fastapi.testclient import TestClient
from app.auth.passwords import gerar_hash
from app.auth.tokens import M2M_AUDIENCE, DISPONIBILIDADE_SCOPE
from app.database.memoria import reset_banco
from app.main import app
from app.settings import get_settings

TOKEN_PATH = "/auth/m2m/token"
DISPONIBILIDADE_PATH = "/disponibilidade"
CONSULTAS_PATH = "/consultas"
CONSULTA_PATH = CONSULTAS_PATH + "/1"
BEARER_PREFIX = "Bearer "


def main():
    destino = Path(__file__).resolve().parent
    names = ["JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "M2M_CLIENT_ID", "M2M_CLIENT_SECRET_HASH", "M2M_TOKEN_MINUTES"]
    anteriores = {name: os.environ.get(name) for name in names}
    registros = []
    try:
        with TemporaryDirectory() as temp:
            senha = token_urlsafe(24)
            secret = token_urlsafe(24)
            cadastro = Path(temp) / "usuarios.json"
            cadastro.write_text(json.dumps([{"username": "profissional1", "papel": "profissional", "profissional_id": 1, "senha_hash": gerar_hash(senha)}]))
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE="123456",
                USERS_FILE=str(cadastro), M2M_CLIENT_ID="laboratorio_parceiro",
                M2M_CLIENT_SECRET_HASH=gerar_hash(secret), M2M_TOKEN_MINUTES="5")
            get_settings.cache_clear()
            reset_banco()
            with TestClient(app) as client:
                def registrar(cenario, response, esperado, *, autentica=False):
                    assert response.status_code == esperado, cenario
                    body = "[token omitido]" if autentica else response.json()
                    registros.append({"cenario": cenario, "metodo": response.request.method,
                        "path": response.request.url.path, "status": response.status_code,
                        "body": body, "www_authenticate": response.headers.get("www-authenticate"),
                        "cache_control": response.headers.get("cache-control")})
                response = client.post(TOKEN_PATH, data={"grant_type": "client_credentials"}, auth=("laboratorio_parceiro", secret))
                registrar("Cliente válido obtém token", response, 200, autentica=True)
                token = response.json()["access_token"]
                headers = {"Authorization": BEARER_PREFIX + token}
                settings = get_settings()
                claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=M2M_AUDIENCE)
                (destino / "claims_publicas.json").write_text(json.dumps({key: claims[key] for key in ["sub", "aud", "iss", "token_use", "client_id", "scope"]}, indent=2) + "\n")
                registrar("Credencial inválida", client.post(TOKEN_PATH, data={"grant_type": "client_credentials"}, auth=("laboratorio_parceiro", "incorreta")), 401)
                registrar("Grant humano rejeitado", client.post(TOKEN_PATH, data={"grant_type": "password"}, auth=("laboratorio_parceiro", secret)), 400)
                registrar("Scope de escrita rejeitado", client.post(TOKEN_PATH, data={"grant_type": "client_credentials", "scope": "consultas:escrever"}, auth=("laboratorio_parceiro", secret)), 400)
                humano = client.post("/auth/token", data={"grant_type": "password", "username": "profissional1", "password": senha})
                registrar("Profissional obtém token distinto", humano, 200, autentica=True)
                human_headers = {"Authorization": BEARER_PREFIX + humano.json()["access_token"]}
                criada = client.post(CONSULTAS_PATH, headers=human_headers, json={"paciente_id": 1, "profissional_id": 1, "data_hora": "2026-10-15T08:15:00", "motivo": "Consulta fictícia"})
                assert criada.status_code == 201
                params = {"dia": "2026-10-15", "profissional_id": 1}
                disponibilidade = client.get(DISPONIBILIDADE_PATH, params=params, headers=headers)
                registrar("Lab lê apenas intervalos livres", disponibilidade, 200)
                assert len(disponibilidade.json()["intervalos"]) == 18
                assert "paciente" not in disponibilidade.text
                registrar("Humano não acessa rota do lab", client.get(DISPONIBILIDADE_PATH, params=params, headers=human_headers), 401)
                registrar("Anônimo não acessa disponibilidade", client.get(DISPONIBILIDADE_PATH, params=params), 401)
                for method, path, body in [
                    ("GET", CONSULTAS_PATH, None), ("GET", CONSULTA_PATH, None),
                    ("POST", CONSULTAS_PATH, {"paciente_id": 1, "profissional_id": 1, "data_hora": "2026-10-15T10:00:00", "motivo": "Tentativa fictícia"}),
                    ("PATCH", CONSULTA_PATH, {"status": "cancelada"}),
                    ("DELETE", CONSULTA_PATH, None), ("GET", "/agenda", None),
                    ("GET", "/admin/status", None), ("POST", "/auth/agenda-session", None),
                ]:
                    argumentos = {"json": body} if body is not None else {}
                    registrar(f"Token M2M bloqueado em {method} {path}", client.request(method, path, headers=headers, **argumentos), 401)
                assert client.get(CONSULTA_PATH, headers=human_headers).json() == criada.json()
                sem_scope = client.post(TOKEN_PATH, data={"grant_type": "client_credentials", "scope": ""}, auth=("laboratorio_parceiro", secret))
                assert sem_scope.status_code == 200
                registrar("Token sem scope não lê disponibilidade", client.get(DISPONIBILIDADE_PATH, params=params, headers={"Authorization": BEARER_PREFIX + sem_scope.json()["access_token"]}), 403)
                registrar("Fim de semana sem expediente", client.get(DISPONIBILIDADE_PATH, params={**params, "dia": "2026-10-17"}, headers=headers), 200)
                registrar("Outro profissional não herda ocupação", client.get(DISPONIBILIDADE_PATH, params={**params, "profissional_id": 2}, headers=headers), 200)
                assert client.patch(CONSULTA_PATH, headers=human_headers, json={"status": "cancelada"}).status_code == 200
                liberada = client.get(DISPONIBILIDADE_PATH, params=params, headers=headers)
                registrar("Cancelamento libera os slots", liberada, 200)
                assert len(liberada.json()["intervalos"]) == 20
            (destino / "respostas_http.json").write_text(json.dumps(registros, indent=2, ensure_ascii=False) + "\n")
            ambiente = {"python": platform.python_version(), "pacotes": {name: version(name) for name in ["fastapi", "PyJWT", "bcrypt", "pydantic-settings", "pytest", "httpx"]}}
            (destino / "ambiente.json").write_text(json.dumps(ambiente, indent=2) + "\n")
            print(f"{len(registros)} cenários M2M verificados; credenciais e bearer omitidos.")
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
