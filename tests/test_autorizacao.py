"""Contratos de identidade, sessão e autorização derivados do threat model."""
import jwt
import pytest
from app.auth.passwords import gerar_hash, verificar_senha
from app.auth.tokens import emitir_token
from app.settings import get_settings

PAYLOAD = {"paciente_id": 1, "profissional_id": 1,
           "data_hora": "2026-10-15T10:00:00", "motivo": "Rotina fictícia"}

@pytest.mark.parametrize("path", ["/consultas", "/consultas/1", "/agenda", "/admin/status"])
def test_anonimo_negado(anonimo, path):
    resposta = anonimo.get(path)
    assert resposta.status_code == 401
    assert resposta.headers["www-authenticate"] == "Bearer"

@pytest.mark.parametrize("username", ["profissional1", "recepcao"])
def test_nao_administrador_negado_na_rota_administrativa(anonimo, autenticar, username):
    assert anonimo.get("/admin/status", headers=autenticar(username)).status_code == 403

@pytest.mark.parametrize("username,password", [
    ("inexistente", "senha-ficticia-testes"), ("profissional1", "incorreta"),
    ("profissional1", "á" * 37),
])
def test_login_invalido_sem_excecao_ou_enumeracao(anonimo, username, password):
    resposta = anonimo.post("/auth/token", data={"grant_type": "password", "username": username, "password": password})
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Credenciais inválidas."}

def test_bcrypt_salt_e_limite_utf8():
    primeiro = gerar_hash("senha-ficticia", rounds=4)
    segundo = gerar_hash("senha-ficticia", rounds=4)
    assert primeiro != segundo
    assert primeiro.startswith("$2b$")
    assert verificar_senha("senha-ficticia", primeiro)
    assert not verificar_senha("outra-senha", primeiro)
    with pytest.raises(ValueError):
        gerar_hash("á" * 37, rounds=4)

@pytest.mark.parametrize("alteracao", [
    {"exp": 1}, {"iss": "outro"}, {"aud": "laboratorio"},
    {"token_use": "m2m_access"}, {"exp": "9999999999"}, {"amr": ["mfa"]}, {"sub": "inexistente"},
])
def test_claims_invalidas_negadas(anonimo, alteracao):
    settings = get_settings()
    token = emitir_token(anonimo.app.state.usuarios["profissional1"], settings)
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=settings.jwt_audience)
    claims.update(alteracao)
    adulterado = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert anonimo.get("/consultas", headers={"Authorization": "Bearer " + adulterado}).status_code == 401

@pytest.mark.parametrize("modo", ["assinatura", "sem_exp", "algoritmo", "adulterado"])
def test_jwt_invalido_negado(anonimo, modo):
    settings = get_settings()
    token = emitir_token(anonimo.app.state.usuarios["profissional1"], settings)
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=settings.jwt_audience)
    key = settings.jwt_secret.get_secret_value()
    algorithm = "HS256"
    if modo == "assinatura":
        key = "chave-ficticia-diferente-com-32-bytes"
    elif modo == "sem_exp":
        del claims["exp"]
    elif modo == "algoritmo":
        algorithm = "HS384"
    if modo == "adulterado":
        token = "invalido.invalido.invalido"
    else:
        token = jwt.encode(claims, key, algorithm=algorithm)
    assert anonimo.get("/consultas", headers={"Authorization": "Bearer " + token}).status_code == 401

def desafio_admin(anonimo):
    resposta = anonimo.post("/auth/token", data={"grant_type": "password", "username": "admin", "password": "senha-ficticia-testes"})
    assert resposta.status_code == 202
    assert "access_token" not in resposta.json()
    assert "123456" not in resposta.text
    return resposta.json()["challenge_id"]

def test_mfa_obrigatorio_uso_unico_e_admin_sem_dados_clinicos(anonimo):
    challenge = desafio_admin(anonimo)
    assert anonimo.get("/admin/status", headers={"Authorization": "Bearer " + challenge}).status_code == 401
    assert anonimo.post("/auth/mfa", json={"challenge_id": challenge, "code": "999999"}).status_code == 401
    resposta = anonimo.post("/auth/mfa", json={"challenge_id": challenge, "code": "123456"})
    assert resposta.status_code == 200
    headers = {"Authorization": "Bearer " + resposta.json()["access_token"]}
    assert anonimo.get("/admin/status", headers=headers).json() == {"status": "online", "servico": "medical-appointment-api"}
    assert anonimo.get("/consultas", headers=headers).status_code == 403
    assert anonimo.get("/agenda", headers=headers).status_code == 403
    assert anonimo.post("/auth/mfa", json={"challenge_id": challenge, "code": "123456"}).status_code == 401

def test_admin_token_sem_mfa_negado(anonimo):
    token = emitir_token(anonimo.app.state.usuarios["admin"], get_settings())
    assert anonimo.get("/admin/status", headers={"Authorization": "Bearer " + token}).status_code == 401

@pytest.mark.parametrize("modo", ["expirado", "cinco_erros", "novo_desafio"])
def test_desafio_inutilizado(anonimo, monkeypatch, modo):
    challenge = desafio_admin(anonimo)
    if modo == "expirado":
        monkeypatch.setattr("app.auth.mfa.monotonic", lambda: float("inf"))
    elif modo == "cinco_erros":
        for _ in range(5):
            assert anonimo.post("/auth/mfa", json={"challenge_id": challenge, "code": "999999"}).status_code == 401
    else:
        desafio_admin(anonimo)
    assert anonimo.post("/auth/mfa", json={"challenge_id": challenge, "code": "123456"}).status_code == 401

def test_ownership_leitura_alteracao_remocao_e_listagem(client, autenticar):
    resposta = client.post("/consultas", json=PAYLOAD)
    assert resposta.status_code == 201
    path = f"/consultas/{resposta.json()['id']}"
    headers = autenticar("profissional2")
    assert client.get(path, headers=headers).status_code == 404
    assert client.patch(path, headers=headers, json={"motivo": "Alteração indevida"}).status_code == 404
    assert client.delete(path, headers=headers).status_code == 404
    assert client.get("/consultas", headers=headers).json() == []
    assert client.get("/consultas?profissional_id=1", headers=headers).json() == []
    assert client.get(path).json() == resposta.json()

@pytest.mark.parametrize("payload,username", [
    ({**PAYLOAD, "profissional_id": 2}, "profissional1"),
    ({**PAYLOAD, "profissional_id": 2}, "profissional2"),
    ({**PAYLOAD, "paciente_id": 999}, "profissional1"),
])
def test_criacao_exige_identidade_e_vinculo_confiavel(anonimo, autenticar, payload, username):
    assert anonimo.post("/consultas", headers=autenticar(username), json=payload).status_code == 403

def test_profissional2_paciente_proprio_e_filtro(client, autenticar):
    headers = autenticar("profissional2")
    assert client.post("/consultas", headers=headers, json={**PAYLOAD, "paciente_id": 2, "profissional_id": 2}).status_code == 201
    assert client.get("/consultas").json() == []
    assert len(client.get("/consultas?paciente_id=2", headers=headers).json()) == 1

def test_cookie_restrito_agenda_e_json_exige_bearer(anonimo, autenticar):
    headers = autenticar("recepcao")
    resposta = anonimo.post("/auth/agenda-session", headers=headers)
    assert resposta.status_code == 204
    cookie = resposta.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "Path=/agenda" in cookie
    assert "SameSite=strict" in cookie
    assert anonimo.get("/agenda").status_code == 200
    assert anonimo.get("/consultas").status_code == 401
    assert anonimo.get("/admin/status").status_code == 401
    assert anonimo.post("/auth/agenda-session").status_code == 401
    assert anonimo.delete("/auth/agenda-session", headers=headers).status_code == 204
    assert anonimo.get("/agenda").status_code == 401

def test_cookie_secure_e_papel_correto(anonimo, autenticar):
    assert anonimo.post("/auth/agenda-session", headers=autenticar("profissional1")).status_code == 403
    settings = get_settings().model_copy(update={"agenda_cookie_secure": True})
    anonimo.app.dependency_overrides[get_settings] = lambda: settings
    try:
        resposta = anonimo.post("/auth/agenda-session", headers=autenticar("recepcao"))
        assert "Secure" in resposta.headers["set-cookie"]
        assert anonimo.get("/agenda").status_code == 401  # cookie Secure não acompanha HTTP
    finally:
        anonimo.app.dependency_overrides.clear()

def test_conta_desativada_invalida_token(anonimo, autenticar):
    headers = autenticar("profissional1")
    conta = anonimo.app.state.usuarios["profissional1"]
    anonimo.app.state.usuarios["profissional1"] = conta.model_copy(update={"ativo": False})
    assert anonimo.get("/consultas", headers=headers).status_code == 401

def test_configuracao_sem_segredo_nao_tem_fallback(monkeypatch):
    from pydantic import ValidationError
    from app.settings import Settings
    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(ValidationError):
        # _env_file pertence ao BaseSettings; os segredos são lidos do ambiente.
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

@pytest.mark.parametrize("username", ["recepcao"])
def test_recepcao_nao_acessa_dados_clinicos(anonimo, autenticar, username):
    headers = autenticar(username)
    assert anonimo.get("/consultas", headers=headers).status_code == 403
    assert anonimo.post("/consultas", headers=headers, json=PAYLOAD).status_code == 403


@pytest.mark.parametrize("modo", ["expirado", "corrompido"])
def test_cookie_invalido_negado(anonimo, autenticar, modo):
    headers = autenticar("recepcao")
    settings = get_settings()
    token = emitir_token(anonimo.app.state.usuarios["recepcao"], settings)
    if modo == "expirado":
        claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=settings.jwt_audience)
        claims["exp"] = 1
        token = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    else:
        token = "invalido"
    anonimo.cookies.set("agenda_session", token, path="/agenda")
    assert anonimo.get("/agenda").status_code == 401


def test_recurso_sem_vinculo_nao_basta_profissional_id(client):
    from app.database.consultas import criar_consulta
    from app.models.consultas import ConsultaCreate
    consulta = criar_consulta(ConsultaCreate(**{**PAYLOAD, "paciente_id": 999}))
    assert client.get(f"/consultas/{consulta.id}").status_code == 404
    assert client.get("/consultas").json() == []


@pytest.mark.parametrize("method,path,payload", [
    ("post", "/consultas", PAYLOAD), ("patch", "/consultas/1", {"status": "cancelada"}),
    ("delete", "/consultas/1", None),
])
def test_mutacoes_sem_token_negadas(anonimo, method, path, payload):
    argumentos = {"json": payload} if payload is not None else {}
    assert anonimo.request(method, path, **argumentos).status_code == 401


def test_configuracao_invalida_nao_expoe_chave_na_excecao(monkeypatch):
    from pydantic import ValidationError
    from app.settings import Settings
    monkeypatch.setenv("JWT_SECRET", "curta-e-sensivel")
    with pytest.raises(ValidationError) as error:
        # _env_file pertence ao BaseSettings; os segredos são lidos do ambiente.
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert "curta-e-sensivel" not in str(error.value)


def test_provisionamento_nao_sobrescreve_cadastro_existente(monkeypatch):
    from app.auth.provision import main
    path = get_settings().users_file
    original = path.read_bytes()
    with pytest.raises(SystemExit, match="não foi sobrescrito"):
        main()
    assert path.read_bytes() == original
