"""Clientes autenticados e estado fictício isolado por teste."""
import json
from secrets import token_urlsafe
import pytest
from fastapi.testclient import TestClient
from app.auth.passwords import gerar_hash
from app.database.memoria import reset_banco
from app.main import app
from app.settings import get_settings

@pytest.fixture(autouse=True)
def ambiente(tmp_path, monkeypatch):
    path = tmp_path / "usuarios.json"
    senha_hash = gerar_hash("senha-ficticia-testes", rounds=4)
    path.write_text(json.dumps([
        dict(username=name, papel=role, profissional_id=prof, senha_hash=senha_hash)
        for name, role, prof in [
            ("profissional1", "profissional", 1), ("profissional2", "profissional", 2),
            ("recepcao", "recepcionista", None), ("admin", "administrador", None),
        ]
    ]))
    monkeypatch.setenv("JWT_SECRET", token_urlsafe(48))
    monkeypatch.setenv("MFA_SIMULATED_CODE", "123456")
    monkeypatch.setenv("USERS_FILE", str(path))
    monkeypatch.setenv("AGENDA_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_banco()
    yield
    reset_banco()
    get_settings.cache_clear()

@pytest.fixture
def anonimo():
    with TestClient(app) as cliente:
        yield cliente

@pytest.fixture
def autenticar(anonimo):
    def login(username):
        resposta = anonimo.post("/auth/token", data={
            "grant_type": "password", "username": username, "password": "senha-ficticia-testes"})
        assert resposta.status_code == 200
        return {"Authorization": "Bearer " + resposta.json()["access_token"]}
    return login

@pytest.fixture
def client(anonimo, autenticar):
    anonimo.headers.update(autenticar("profissional1"))
    return anonimo

@pytest.fixture
def recepcao_headers(autenticar):
    return autenticar("recepcao")
