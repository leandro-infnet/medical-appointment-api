"""Ampliação dos cenários de autorização do Ex. 6 a partir de TM do Ex. 4."""
import jwt
import pytest
from app.settings import get_settings

CONSULTAS = "/consultas"
PAYLOAD = {"paciente_id": 1, "profissional_id": 1, "data_hora": "2026-10-15T09:00:00",
           "motivo": "Dado clínico fictício"}


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_tm002_tm003_acesso_cruzado_mesmo_erro_sem_efeito(client, autenticar, method):
    criada = client.post(CONSULTAS, json=PAYLOAD)
    assert criada.status_code == 201
    outro = autenticar("profissional2")
    body = {"json": {"motivo": "Mutação indevida fictícia"}} if method == "PATCH" else {}
    existente = client.request(method, "/consultas/1", headers=outro, **body)
    ausente = client.request(method, "/consultas/999", headers=outro, **body)
    assert existente.status_code == 404
    assert ausente.status_code == 404
    assert existente.json() == ausente.json()
    assert client.get("/consultas/1").json() == criada.json()
    assert client.get(CONSULTAS, headers=outro).json() == []


def test_tm013_claim_papel_e_mfa_nao_substituem_papel_confiavel(anonimo, autenticar):
    headers = autenticar("profissional1")
    settings = get_settings()
    claims = jwt.decode(headers["Authorization"].removeprefix("Bearer "), settings.jwt_secret.get_secret_value(),
                        algorithms=["HS256"], audience=settings.jwt_audience)
    # Mesmo token assinado em ensaio controlado não pode criar privilégios pelo claim extra.
    claims.update(papel="administrador", amr=["pwd", "mfa"])
    token = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    resposta = anonimo.get("/admin/status", headers={"Authorization": "Bearer " + token})
    assert resposta.status_code == 403


def test_tm006_tm011_erro_nao_grava_nem_repete_campo_extra(client):
    marcador = "NOTA-FICTICIA-QUE-NAO-DEVE-SER-ECOADA"
    response = client.post(CONSULTAS, json={**PAYLOAD, "prontuario": marcador})
    assert response.status_code == 422
    assert marcador not in response.text
    assert client.get(CONSULTAS).json() == []
