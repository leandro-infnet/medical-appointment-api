"""Headers, CORS e abuso controlado em processo, sem servidor ou dados reais."""
import html
import json
import os
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from secrets import randbelow, token_urlsafe
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.auth.passwords import gerar_hash
from app.main import app
from app.settings import get_settings

DESTINO = Path(__file__).resolve().parent
ORIGIN = "http://localhost:5173"
LOGIN = "/auth/token"
CONSULTAS = "/consultas"
PUBLIC_HEADERS = ("x-frame-options", "x-content-type-options", "strict-transport-security",
                  "access-control-allow-origin", "access-control-expose-headers", "retry-after")


def registrar(casos, nome, response, expected):
    assert response.status_code == expected, nome
    casos.append({"cenario": nome, "metodo": response.request.method,
                  "url": str(response.request.url), "status": response.status_code,
                  "headers": {name: response.headers.get(name) for name in PUBLIC_HEADERS}})


def verificar(senha):
    casos = []
    form = {"grant_type": "password", "username": "profissional1", "password": senha}
    with TestClient(app, base_url="https://clinica.example") as client:
        for path, expected in [("/", 200), (CONSULTAS, 401), ("/inexistente", 404)]:
            response = client.get(path)
            registrar(casos, "HTTPS em processo: " + path, response, expected)
            assert response.headers["strict-transport-security"] == "max-age=31536000"
        registrar(casos, "Erro de formulário também recebe headers", client.post(LOGIN, data={}), 422)
        preflight = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
                     "Access-Control-Request-Headers": "authorization,content-type"}
        registrar(casos, "Preflight permitido sem JWT", client.options(CONSULTAS, headers=preflight), 200)
        registrar(casos, "Preflight com origem negada", client.options(CONSULTAS, headers={
            **preflight, "Origin": "https://externa.example"}), 400)
        permitida = client.get(CONSULTAS, headers={"Origin": ORIGIN})
        registrar(casos, "Origem permitida não contorna autenticação", permitida, 401)
        assert permitida.headers["access-control-allow-origin"] == ORIGIN
        negada = client.get("/", headers={"Origin": "https://externa.example"})
        registrar(casos, "GET externo continua HTTP válido sem concessão CORS", negada, 200)
        assert "access-control-allow-origin" not in negada.headers
    with TestClient(app) as client:
        response = client.get("/")
        registrar(casos, "HTTP local: sem política HSTS", response, 200)
        assert "strict-transport-security" not in response.headers
    with TestClient(app, base_url="https://clinica.example") as client:
        clock = [100.0]
        app.state.rate_limiter.clock = lambda: clock[0]
        for i in range(20):
            expected = 401 if i < 5 else 429
            response = client.post(LOGIN, data={**form, "password": senha + "-incorreta"},
                headers={"Origin": ORIGIN, "X-Forwarded-For": f"192.0.2.{i}"})
            registrar(casos, f"VUL-003: tentativa inválida {i + 1}/20", response, expected)
        response = client.post(LOGIN, data=form)
        registrar(casos, "Credencial correta também aguarda janela esgotada", response, 429)
        assert response.headers["retry-after"] == "60"
        registrar(casos, "MFA compartilha cota", client.post("/auth/mfa", json={}), 429)
        registrar(casos, "M2M compartilha cota", client.post("/auth/m2m/token", data={}), 429)
        for _ in range(60):
            assert client.get("/").status_code == 200
        registrar(casos, "Rota comum admite 60, depois bloqueia", client.get("/"), 429)
        clock[0] = 160.0
        registrar(casos, "Login correto recupera após 60s simulados", client.post(LOGIN, data=form), 200)
        registrar(casos, "Rota comum recupera após janela", client.get("/"), 200)
    return casos


def main():
    names = ("JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "M2M_CLIENT_SECRET_HASH",
             "CORS_ORIGINS", "LOGIN_RATE_LIMIT", "GENERAL_RATE_LIMIT")
    anteriores = {name: os.environ.get(name) for name in names}
    try:
        with TemporaryDirectory() as temp:
            senha = token_urlsafe(24)
            arquivo = Path(temp) / "usuarios.json"
            arquivo.write_text(json.dumps([{"username": "profissional1", "papel": "profissional",
                "profissional_id": 1, "senha_hash": gerar_hash(senha)}]))
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE=f"{randbelow(1000000):06d}",
                USERS_FILE=str(arquivo), M2M_CLIENT_SECRET_HASH="", CORS_ORIGINS=json.dumps([ORIGIN]),
                LOGIN_RATE_LIMIT="5", GENERAL_RATE_LIMIT="60")
            get_settings.cache_clear()
            casos = verificar(senha)
    finally:
        for name, value in anteriores.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        get_settings.cache_clear()
    resultado = {"casos": casos, "configuracao": {"cors_origins": [ORIGIN],
        "login_rate_limit": 5, "general_rate_limit": 60, "janela_segundos": 60},
        "limites": ["HTTPS simulado pelo TestClient; nenhum certificado ou handshake TLS verificado.",
                    "Contador local por arranque; não coordena workers nem mede capacidade.",
                    "Nenhum token, senha, código MFA ou hash foi incluído."]}
    (DESTINO / "respostas_http.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    (DESTINO / "hardening.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<title>Ex. 10 — hardening</title><h1>Verificações de rede e abuso</h1><pre>'
        + html.escape(json.dumps(resultado, ensure_ascii=False, indent=2)) + '</pre></html>\n')
    ambiente = {"python": platform.python_version(), "pacotes": {name: version(name)
        for name in ("fastapi", "starlette", "pydantic-settings", "pytest", "httpx")}}
    (DESTINO / "ambiente.json").write_text(json.dumps(ambiente, indent=2) + "\n")
    print(f"{len(casos)} observações verificadas; 20 tentativas de senha e cota geral de 60 incluídas.")
    print("HTTPS somente em processo; segredos omitidos; nenhum scan ou deploy executado.")


if __name__ == "__main__":
    main()
