"""Contratos de entrada e integração entre middleware JWT e ownership."""
from unittest.mock import patch

import pytest

from app.auth.dependencies import identidade

CONSULTAS = "/consultas"
PAYLOAD = {"paciente_id": 1, "profissional_id": 1,
           "data_hora": "2026-10-15T10:00:00", "motivo": "Avaliação fictícia"}


@pytest.mark.parametrize("campo", ["papel", "paciente_id", "profissional_id", "id", "criado_em"])
def test_patch_rejeita_campos_fora_do_contrato_sem_mutar(client, campo):
    criada = client.post(CONSULTAS, json=PAYLOAD).json()
    path = f"{CONSULTAS}/{criada['id']}"
    resposta = client.patch(path, json={"motivo": "Alteração fictícia", campo: 2})
    assert resposta.status_code == 422
    assert any(error["type"] == "extra_forbidden" for error in resposta.json()["detail"])
    assert client.get(path).json() == criada


def test_create_rejeita_extra_sem_criar(client):
    response = client.post(CONSULTAS, json={**PAYLOAD, "papel": "administrador"})
    assert response.status_code == 422
    assert client.get(CONSULTAS).json() == []


@pytest.mark.parametrize("estado", ["agendada", "cancelada", "realizada"])
def test_estados_permitidos(client, estado):
    criada = client.post(CONSULTAS, json=PAYLOAD).json()
    response = client.patch(f"{CONSULTAS}/{criada['id']}", json={"status": estado})
    assert response.status_code == 200
    assert response.json()["status"] == estado


@pytest.mark.parametrize("estado", [None, "", "confirmada", "AGENDADA", "<script>alert(1)</script>"])
def test_status_invalido_nao_muta(client, estado):
    criada = client.post(CONSULTAS, json=PAYLOAD).json()
    path = f"{CONSULTAS}/{criada['id']}"
    assert client.patch(path, json={"status": estado}).status_code == 422
    assert client.get(path).json() == criada


@pytest.mark.parametrize("nome", ["ADMIN", "a b", "a\n", "x' OR '1'='1", "á", "a" * 65])
def test_username_rejeita_formato(anonimo, nome):
    response = anonimo.post("/auth/token", data={"grant_type": "password",
                                                "username": nome, "password": "invalid"})
    assert response.status_code == 422
    assert "access_token" not in response.json()


def test_texto_clinico_preserva_acentos_pontuacao_e_literal_sql(client):
    motivo = "Avaliação: dor d'água; ' OR 1=1 --"
    response = client.post(CONSULTAS, json={**PAYLOAD, "motivo": motivo})
    assert response.status_code == 201
    assert response.json()["motivo"] == motivo
    assert len(client.get(CONSULTAS).json()) == 1


def test_jwt_validado_uma_vez_e_ownership_nao_depende_so_do_token(client, autenticar):
    criada = client.post(CONSULTAS, json=PAYLOAD).json()
    outro = autenticar("profissional2")
    path = f"{CONSULTAS}/{criada['id']}"
    with patch("app.auth.middleware.identidade", wraps=identidade) as validar:
        assert client.get(path).status_code == 200
        assert validar.call_count == 1
        validar.reset_mock()
        assert client.patch(path, headers=outro, json={"motivo": "Alteração fictícia"}).status_code == 404
        assert validar.call_count == 1
    assert client.get(path).json() == criada


def test_middleware_autentica_antes_de_validar_corpo(anonimo):
    response = anonimo.post(CONSULTAS, json={"campo": "inválido"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_header_invalido_nao_cai_para_cookie_valido(anonimo, recepcao_headers):
    assert anonimo.post("/auth/agenda-session", headers=recepcao_headers).status_code == 204
    assert anonimo.get("/agenda").status_code == 200
    assert anonimo.get("/agenda", headers={"Authorization": "Basic abc"}).status_code == 401


def test_openapi_publica_allowlist_e_rejeicao_de_extras(anonimo):
    spec = anonimo.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]
    assert schemas["ConsultaCreate"]["additionalProperties"] is False
    assert schemas["ConsultaUpdate"]["additionalProperties"] is False
    assert schemas["ConsultaUpdate"]["properties"]["status"]["anyOf"][0]["enum"] == [
        "agendada", "cancelada", "realizada"]
    assert spec["paths"]["/auth/token"]["post"]["responses"]["429"]["headers"]["Retry-After"]["schema"]["type"] == "integer"


@pytest.mark.parametrize("extra", ["papel", "client_id", "client_secret", "paciente_id"])
def test_endpoint_adicional_m2m_rejeita_extras(anonimo, extra):
    response = anonimo.post("/auth/m2m/token", auth=("laboratorio_parceiro", "senha-ficticia-testes"),
                           data={"grant_type": "client_credentials", extra: "ficticio"})
    assert response.status_code == 422
    assert any(error["type"] == "extra_forbidden" for error in response.json()["detail"])
    assert "access_token" not in response.json()


@pytest.mark.parametrize("formulario", [False, True])
def test_erro_validacao_nao_repete_valor_sensivel(client, formulario):
    marcador = "DADO-SENSIVEL-FICTICIO-NAO-REPETIR"
    if formulario:
        response = client.post("/auth/m2m/token", auth=("laboratorio_parceiro", "senha-ficticia-testes"),
                               data={"grant_type": "client_credentials", "client_secret": marcador})
    else:
        response = client.post(CONSULTAS, json={**PAYLOAD, "campo_extra": marcador})
    assert response.status_code == 422
    assert marcador not in response.text
    assert all(set(error) == {"loc", "type", "msg"} for error in response.json()["detail"])
