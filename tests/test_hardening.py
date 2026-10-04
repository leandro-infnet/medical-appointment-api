"""Rede e abuso: limites reais, relógio controlado e credenciais fictícias."""
from secrets import token_urlsafe

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.main import app
from app.network import RateLimiter
from app.settings import Settings

ORIGIN = "http://localhost:5173"
LOGIN = "/auth/token"
FORM = {"grant_type": "password", "username": "profissional1", "password": "senha-ficticia-testes"}


def test_preflight_permitido_sem_jwt_e_sem_consumir_cotas(anonimo):
    headers = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "authorization,content-type"}
    for _ in range(7):
        response = anonimo.options("/consultas", headers=headers)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ORIGIN
        assert "access-control-allow-credentials" not in response.headers
    assert anonimo.app.state.rate_limiter.requests == {}


@pytest.mark.parametrize("changes", [
    {"Origin": "https://origem-nao-permitida.example"},
    {"Origin": "http://127.0.0.1:5173"},
    {"Origin": ORIGIN + ".example"},
    {"Access-Control-Request-Method": "PUT"},
    {"Access-Control-Request-Headers": "x-nao-permitido"},
])
def test_preflight_rejeita_origem_metodo_ou_header(anonimo, changes):
    headers = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST", **changes}
    response = anonimo.options("/consultas", headers=headers)
    assert response.status_code == 400
    assert response.headers["x-frame-options"] == "DENY"
    if headers["Origin"] != ORIGIN:
        assert "access-control-allow-origin" not in response.headers


def test_cors_nao_substitui_autenticacao(anonimo):
    response = anonimo.get("/consultas", headers={"Origin": ORIGIN})
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "Origin" in response.headers["vary"]
    response = anonimo.get("/", headers={"Origin": "https://externa.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("method,path,data,expected", [
    ("GET", "/", None, 200), ("GET", "/inexistente", None, 404),
    ("GET", "/consultas", None, 401), ("POST", LOGIN, {"username": "a"}, 422),
])
def test_headers_https_em_sucesso_e_erros(method, path, data, expected):
    with TestClient(app, base_url="https://clinica.example") as client:
        response = client.request(method, path, data=data)
        assert response.status_code == expected
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["strict-transport-security"] == "max-age=31536000"


def test_http_local_nao_emite_hsts(anonimo):
    response = anonimo.get("/")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "strict-transport-security" not in response.headers


def test_agenda_autenticada_e_proibicao_tem_headers_https():
    with TestClient(app, base_url="https://clinica.example") as client:
        response = client.post(LOGIN, data={**FORM, "username": "recepcao"})
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        agenda = client.get("/agenda", headers=headers)
        assert agenda.status_code == 200
        assert agenda.headers["strict-transport-security"] == "max-age=31536000"
        assert agenda.headers["x-frame-options"] == "DENY"
        assert agenda.headers["x-content-type-options"] == "nosniff"
        proibida = client.get("/consultas", headers=headers)
        assert proibida.status_code == 403
        assert proibida.headers["strict-transport-security"] == "max-age=31536000"


def test_limite_login_recupera_janela_e_cors_no_429(anonimo):
    clock = [100.0]
    anonimo.app.state.rate_limiter.clock = lambda: clock[0]
    for _ in range(5):
        assert anonimo.post(LOGIN, data=FORM).status_code == 200
    response = anonimo.post(LOGIN, data=FORM, headers={"Origin": ORIGIN})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["access-control-expose-headers"] == "Retry-After"
    assert response.headers["cache-control"] == "no-store"
    clock[0] += 59.1
    assert anonimo.post(LOGIN, data=FORM).headers["retry-after"] == "1"
    clock[0] = 160
    assert anonimo.post(LOGIN, data=FORM).status_code == 200


def test_tentativas_invalidas_e_forwarded_for_nao_contornam_cota(anonimo):
    for i in range(5):
        response = anonimo.post(LOGIN, data={**FORM, "password": token_urlsafe(24)},
                               headers={"X-Forwarded-For": f"192.0.2.{i}"})
        assert response.status_code == 401
    assert anonimo.post(LOGIN, data=FORM, headers={"X-Forwarded-For": "192.0.2.99"}).status_code == 429


def test_mfa_m2m_e_login_compartilham_cota(anonimo):
    for _ in range(5):
        assert anonimo.post(LOGIN, data=FORM).status_code == 200
    assert anonimo.post("/auth/mfa", json={}).status_code == 429
    assert anonimo.post("/auth/m2m/token", data={"grant_type": "client_credentials"}).status_code == 429
    assert anonimo.get("/").status_code == 200


def test_rota_comum_sessenta_requisicoes_e_cota_independente(anonimo):
    for _ in range(60):
        assert anonimo.get("/").status_code == 200
    assert anonimo.get("/").status_code == 429
    assert anonimo.post(LOGIN, data=FORM).status_code == 200


def test_headers_no_429_https():
    with TestClient(app, base_url="https://clinica.example") as client:
        for _ in range(5):
            assert client.post(LOGIN, data=FORM).status_code == 200
        response = client.post(LOGIN, data=FORM)
        assert response.status_code == 429
        assert response.headers["strict-transport-security"] == "max-age=31536000"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-content-type-options"] == "nosniff"


def test_contador_isola_ip_e_elimina_clientes_inativos():
    clock = [0.0]
    limiter = RateLimiter(5, 60, lambda: clock[0])
    for _ in range(5):
        assert limiter.retry_after("192.0.2.1", "credenciais") == 0
    assert limiter.retry_after("192.0.2.1", "credenciais") == 60
    assert limiter.retry_after("192.0.2.2", "credenciais") == 0
    clock[0] = 60
    assert limiter.retry_after("192.0.2.2", "credenciais") == 0
    assert ("192.0.2.1", "credenciais") not in limiter.requests


def test_estado_reiniciado_no_proximo_arranque():
    for _ in range(2):
        with TestClient(app) as client:
            for _ in range(5):
                assert client.post(LOGIN, data=FORM).status_code == 200


@pytest.mark.parametrize("origins", [["*"], ["null"], [], ["https://example.org/path"],
    ["https://user:secret@example.org"], ["https://example.org:99999"], ["http://localhost:5173/"]])
def test_configuracao_rejeita_origens_invalidas(origins):
    jwt_secret = SecretStr(token_urlsafe(48))
    mfa_code = SecretStr("654321")
    with pytest.raises(ValidationError):
        Settings(jwt_secret=jwt_secret, mfa_simulated_code=mfa_code, cors_origins=origins)


@pytest.mark.parametrize("login,general", [(0, 60), (5, 0), (5, 5), (60, 5)])
def test_configuracao_preserva_limite_diferenciado(login, general):
    jwt_secret = SecretStr(token_urlsafe(48))
    mfa_code = SecretStr("654321")
    with pytest.raises(ValidationError):
        Settings(jwt_secret=jwt_secret, mfa_simulated_code=mfa_code,
                 login_rate_limit=login, general_rate_limit=general)
