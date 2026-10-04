"""Restrição de Client Credentials, claims/scopes e contrato de disponibilidade."""
import jwt
import pytest
from app.auth.tokens import M2M_AUDIENCE
from app.settings import get_settings

TOKEN_PATH = "/auth/m2m/token"
DISPONIBILIDADE_PATH = "/disponibilidade"
SCOPE = "disponibilidade:ler"
PARAMS = {"dia": "2026-10-15", "profissional_id": 1}
PAYLOAD = {"paciente_id": 1, "profissional_id": 1, "data_hora": "2026-10-15T08:15:00", "motivo": "Informação clínica fictícia"}


def obter_token(client, *, scope=None):
    form = {"grant_type": "client_credentials"}
    if scope is not None:
        form["scope"] = scope
    resposta = client.post(TOKEN_PATH, data=form, auth=("laboratorio_parceiro", "senha-ficticia-testes"))
    assert resposta.status_code == 200
    return resposta


def bearer(token):
    return {"Authorization": "Bearer " + token}


def test_client_credentials_e_claims_distintos(anonimo):
    resposta = obter_token(anonimo)
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json()["scope"] == SCOPE
    assert resposta.json()["expires_in"] == 300
    settings = get_settings()
    claims = jwt.decode(resposta.json()["access_token"], settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=M2M_AUDIENCE)
    assert claims["sub"] == "client:laboratorio_parceiro"
    assert claims["client_id"] == "laboratorio_parceiro"
    assert claims["token_use"] == "m2m_access"
    assert claims["scope"] == SCOPE
    assert "amr" not in claims
    assert "papel" not in claims

@pytest.mark.parametrize("auth", [None, ("outro", "senha-ficticia-testes"), ("laboratorio_parceiro", "incorreta"), ("laboratorio_parceiro", "á" * 37)])
def test_cliente_invalido_negado(anonimo, auth):
    response = anonimo.post(TOKEN_PATH, data={"grant_type": "client_credentials"}, auth=auth)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"

@pytest.mark.parametrize("grant,scope,error", [
    ("password", SCOPE, "unsupported_grant_type"),
    ("client_credentials", "consultas:escrever", "invalid_scope"),
    ("client_credentials", SCOPE + " admin", "invalid_scope"),
])
def test_grant_scope_nao_ampliam_poder(anonimo, grant, scope, error):
    response = anonimo.post(TOKEN_PATH, auth=("laboratorio_parceiro", "senha-ficticia-testes"), data={"grant_type": grant, "scope": scope})
    assert response.status_code == 400
    assert response.json()["error"] == error

@pytest.mark.parametrize("changes", [{"exp": 1}, {"aud": "clinic-human-clients"}, {"token_use": "human_access"}, {"sub": "profissional1"}, {"client_id": "outro"}, {"scope": []}])
def test_claims_m2m_invalidas(anonimo, changes):
    settings = get_settings()
    token = obter_token(anonimo).json()["access_token"]
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=M2M_AUDIENCE)
    claims.update(changes)
    forged = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(forged)).status_code == 401

@pytest.mark.parametrize("scope", ["", "consultas:escrever", SCOPE + " admin"])
def test_scope_insuficiente_ou_excessivo_negado(anonimo, scope):
    token = obter_token(anonimo, scope="").json()["access_token"]
    settings = get_settings()
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=M2M_AUDIENCE)
    claims["scope"] = scope
    token = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    resposta = anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(token))
    assert resposta.status_code == 403
    assert "insufficient_scope" in resposta.headers["www-authenticate"]

@pytest.mark.parametrize("method,path,json_body", [
    ("GET", "/consultas", None), ("GET", "/consultas/1", None),
    ("POST", "/consultas", PAYLOAD), ("PATCH", "/consultas/1", {"status": "cancelada"}),
    ("DELETE", "/consultas/1", None), ("GET", "/agenda", None),
    ("GET", "/admin/status", None), ("POST", "/auth/agenda-session", None),
])
def test_token_m2m_nao_acessa_rotas_humanas(anonimo, method, path, json_body):
    headers = bearer(obter_token(anonimo).json()["access_token"])
    kwargs = {"json": json_body} if json_body is not None else {}
    assert anonimo.request(method, path, headers=headers, **kwargs).status_code == 401

@pytest.mark.parametrize("username", ["profissional1", "recepcao"])
def test_token_humano_nao_acessa_disponibilidade(anonimo, autenticar, username):
    assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=autenticar(username)).status_code == 401


def test_disponibilidade_sem_dados_clinicos_e_com_sobreposicao(client):
    assert client.post("/consultas", json=PAYLOAD).status_code == 201
    token = obter_token(client).json()["access_token"]
    response = client.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(token))
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"profissional_id", "dia", "fuso", "intervalos"}
    assert len(data["intervalos"]) == 18  # 08:15–08:45 bloqueia dois slots.
    assert data["intervalos"][0] == {"inicio": "2026-10-15T09:00:00-03:00", "fim": "2026-10-15T09:30:00-03:00"}
    assert set(data["intervalos"][0]) == {"inicio", "fim"}
    assert "paciente" not in response.text
    assert "motivo" not in response.text


def test_cancelada_libera_outros_estados_bloqueiam_e_profissionais_isolados(client):
    criada = client.post("/consultas", json=PAYLOAD)
    path = f"/consultas/{criada.json()['id']}"
    headers = bearer(obter_token(client).json()["access_token"])
    def slots(profissional=1):
        response = client.get(DISPONIBILIDADE_PATH, params={**PARAMS, "profissional_id": profissional}, headers=headers)
        assert response.status_code == 200
        return response.json()["intervalos"]
    assert len(slots(2)) == 20
    for estado in ["agendada", "realizada"]:
        assert client.patch(path, json={"status": estado}).status_code == 200
        assert len(slots()) == 18
    assert client.patch(path, json={"status": "estado-desconhecido"}).status_code == 422
    # Dado legado desconhecido continua bloqueando por precaução.
    from app.database.memoria import _consultas, _lock
    with _lock:
        _consultas[criada.json()["id"]]["status"] = "estado-desconhecido"
    assert len(slots()) == 18
    assert client.patch(path, json={"status": "cancelada"}).status_code == 200
    assert len(slots()) == 20


def test_disponibilidade_utc_limites_e_fim_de_semana(client):
    assert client.post("/consultas", json={**PAYLOAD, "data_hora": "2026-10-15T10:45:00Z"}).status_code == 201  # 07:45 local → bloqueia 08h.
    assert client.post("/consultas", json={**PAYLOAD, "data_hora": "2026-10-15T18:00:00-03:00"}).status_code == 201
    headers = bearer(obter_token(client).json()["access_token"])
    response = client.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=headers)
    assert len(response.json()["intervalos"]) == 19
    assert response.json()["intervalos"][0]["inicio"] == "2026-10-15T08:30:00-03:00"
    assert client.get(DISPONIBILIDADE_PATH, params={**PARAMS, "dia": "2026-10-17"}, headers=headers).json()["intervalos"] == []


def test_parametros_e_anonimo_negados(anonimo):
    assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS).status_code == 401
    headers = bearer(obter_token(anonimo).json()["access_token"])
    assert anonimo.get(DISPONIBILIDADE_PATH, params={**PARAMS, "dia": "2026-02-30"}, headers=headers).status_code == 422
    assert anonimo.get(DISPONIBILIDADE_PATH, params={**PARAMS, "profissional_id": 0}, headers=headers).status_code == 422
    assert anonimo.get(DISPONIBILIDADE_PATH, params={**PARAMS, "profissional_id": 999}, headers=headers).status_code == 404


def test_cliente_desativado_sem_fallback(anonimo, monkeypatch):
    token = obter_token(anonimo).json()["access_token"]
    settings = get_settings().model_copy(update={"m2m_client_secret_hash": None})
    # Middleware ASGI executa antes da resolução de Depends do FastAPI.
    monkeypatch.setattr("app.auth.middleware.get_settings", lambda: settings)
    anonimo.app.dependency_overrides[get_settings] = lambda: settings
    try:
        assert anonimo.post(TOKEN_PATH, data={"grant_type": "client_credentials"}, auth=("laboratorio_parceiro", "senha-ficticia-testes")).status_code == 401
        assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(token)).status_code == 401
    finally:
        anonimo.app.dependency_overrides.clear()


def test_openapi_client_credentials_e_scope(anonimo):
    schema = anonimo.get("/openapi.json").json()
    flow = schema["components"]["securitySchemes"]["LaboratorioOAuth2"]["flows"]["clientCredentials"]
    assert flow["tokenUrl"] == "auth/m2m/token"
    assert schema["paths"][TOKEN_PATH]["post"]["security"] == [{"ClientCredentialsAuthentication": []}]
    assert set(flow["scopes"]) == {SCOPE}
    assert schema["paths"][DISPONIBILIDADE_PATH]["get"]["security"] == [{"LaboratorioOAuth2": [SCOPE]}]


@pytest.mark.parametrize("modo", ["assinatura", "sem_scope", "algoritmo", "adulterado"])
def test_token_cliente_invalido_criptografia_e_claim_obrigatoria(anonimo, modo):
    settings = get_settings()
    token = obter_token(anonimo).json()["access_token"]
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=M2M_AUDIENCE)
    key = settings.jwt_secret.get_secret_value()
    algorithm = "HS256"
    if modo == "assinatura":
        key = "outra-chave-ficticia-com-32-bytes-ou-mais"
    elif modo == "sem_scope":
        del claims["scope"]
    elif modo == "algoritmo":
        algorithm = "HS384"
    token = "invalido.invalido.invalido" if modo == "adulterado" else jwt.encode(claims, key, algorithm=algorithm)
    assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(token)).status_code == 401


def test_credenciais_no_corpo_e_basic_malformado_nao_autenticam(anonimo):
    response = anonimo.post(TOKEN_PATH, data={"grant_type": "client_credentials", "client_id": "laboratorio_parceiro", "client_secret": "senha-ficticia-testes"})
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_client"}
    response = anonimo.post(TOKEN_PATH, data={"grant_type": "client_credentials"}, headers={"Authorization": "Basic !!!"})
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_client"}


@pytest.mark.parametrize("scope", [SCOPE, ""])
def test_scope_explicito_sem_refresh_e_pacientes(anonimo, scope):
    response = obter_token(anonimo, scope=scope)
    assert "refresh_token" not in response.json()
    assert response.json()["scope"] == scope
    assert response.headers["pragma"] == "no-cache"


def test_scope_falso_em_token_humano_nao_vira_laboratorio(anonimo):
    from app.auth.tokens import emitir_token
    settings = get_settings()
    token = emitir_token(anonimo.app.state.usuarios["profissional1"], settings)
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=settings.jwt_audience)
    claims.update(scope=SCOPE, aud=M2M_AUDIENCE, client_id=settings.m2m_client_id)
    token = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert anonimo.get(DISPONIBILIDADE_PATH, params=PARAMS, headers=bearer(token)).status_code == 401
