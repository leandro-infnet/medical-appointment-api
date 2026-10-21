"""Unidades de entrada/autorização e contratos HTTP do capstone."""
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError, SecretStr
from app.auth import policies
from app.models.consultas import Consulta, ConsultaCreate
from app.models.identidades import Papel, Usuario
from app.routes.consultas import endpoint_criar_consulta


def conta(papel=Papel.PROFISSIONAL):
    return Usuario(username="ficticio", papel=papel, senha_hash=SecretStr("hash-ficticio"),
                   profissional_id=1 if papel == Papel.PROFISSIONAL else None)


def dados():
    return {"paciente_id": 1, "profissional_id": 1, "data_hora": "2026-10-20T09:00:00",
            "motivo": "Rotina fictícia"}


def test_criacao_valida_delega_ao_banco():
    entrada = ConsultaCreate.model_validate(dados())
    session = Mock()
    consulta = Consulta.model_validate({"id": 1, **dados()})
    with patch("app.routes.consultas.criar_consulta", return_value=consulta) as criar:
        assert endpoint_criar_consulta(entrada, conta(), session) == consulta
    criar.assert_called_once_with(session, entrada)


@pytest.mark.parametrize("alteracao", [{"paciente_id": 0}, {"motivo": "ab"},
                                        {"papel": "administrador"}])
def test_entrada_invalida_nao_chega_ao_banco(alteracao):
    payload = {**dados(), **alteracao}
    with patch("app.routes.consultas.criar_consulta") as criar:
        with pytest.raises(ValidationError):
            ConsultaCreate.model_validate(payload)
    criar.assert_not_called()


def test_vinculo_alheio_impede_gravacao():
    entrada = ConsultaCreate.model_validate({**dados(), "paciente_id": 3, "profissional_id": 2})
    usuario = conta()
    session = Mock()
    with patch("app.routes.consultas.criar_consulta") as criar:
        with pytest.raises(HTTPException) as erro:
            endpoint_criar_consulta(entrada, usuario, session)
    assert erro.value.status_code == 403
    criar.assert_not_called()


@pytest.mark.parametrize("paciente,profissional", [(3, 2), (999, 1)])
def test_ownership_usa_recurso_carregado_do_banco(paciente, profissional):
    consulta = Consulta.model_validate({"id": 5, **dados(), "paciente_id": paciente,
                                       "profissional_id": profissional})
    usuario = conta()
    with patch("app.auth.policies.obter_consulta_por_id", return_value=consulta) as obter:
        session = Mock()
        with pytest.raises(HTTPException) as erro:
            policies.consulta_autorizada(5, usuario, session)
    assert erro.value.status_code == 404
    obter.assert_called_once_with(session, 5)


def test_recurso_inexistente_mesmo_404():
    usuario = conta()
    session = Mock()
    with patch("app.auth.policies.obter_consulta_por_id", return_value=None):
        with pytest.raises(HTTPException) as erro:
            policies.consulta_autorizada(999, usuario, session)
    assert erro.value.status_code == 404


def test_administracao_nega_recepcionista():
    usuario = conta(Papel.RECEPCAO)
    with pytest.raises(HTTPException) as erro:
        policies.exigir_papel(usuario, Papel.ADMIN)
    assert erro.value.status_code == 403


def test_openapi_contratos_de_entrada_saida_e_scopes(anonimo):
    schema = anonimo.get("/openapi.json").json()
    models = schema["components"]["schemas"]
    for nome in ("ConsultaCreate", "ConsultaUpdate", "MFAInput", "M2MTokenInput"):
        assert models[nome]["additionalProperties"] is False
    publicos = models["ConsultaResponse"]["properties"]
    for campo in ("observacoes_internas", "criado_em", "atualizado_em", "senha_hash"):
        assert campo not in publicos
    paths = schema["paths"]
    assert paths["/consultas"]["post"]["security"] == [{"OAuth2PasswordBearer": []}]
    assert paths["/disponibilidade"]["get"]["security"] == [
        {"LaboratorioOAuth2": ["disponibilidade:ler"]}]
    for path in ("/auth/token", "/auth/mfa", "/"):
        assert not paths[path]["post" if path.startswith("/auth") else "get"].get("security")


@pytest.mark.parametrize("path", ["/agenda", "/admin/status", "/auth/agenda-session"])
def test_openapi_documenta_erros_de_acesso_reais(anonimo, path):
    methods = ["post", "delete"] if path.startswith("/auth") else ["get"]
    paths = anonimo.get("/openapi.json").json()["paths"]
    for method in methods:
        responses = paths[path][method]["responses"]
        assert "401" in responses
        assert "403" in responses
    response = anonimo.request(methods[0], path)
    assert response.status_code == 401


def test_openapi_agenda_aceita_bearer_ou_cookie(anonimo):
    schema = anonimo.get("/openapi.json").json()
    assert schema["paths"]["/agenda"]["get"]["security"] == [
        {"OAuth2PasswordBearer": []}, {"AgendaCookie": []}]
    assert schema["components"]["securitySchemes"]["AgendaCookie"]["in"] == "cookie"


def test_respostas_clinicas_nao_permanecem_em_cache(client, autenticar):
    assert client.get("/consultas").headers["cache-control"] == "no-store"
    response = client.get("/agenda", headers=autenticar("recepcao"))
    assert response.status_code == 200
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_login_incorreto_nao_emite_token():
    from fastapi import Response
    from fastapi.security import OAuth2PasswordRequestFormStrict
    from app.routes.auth import login
    from app.settings import get_settings

    usuario = conta()
    form = OAuth2PasswordRequestFormStrict(grant_type="password",
        username=usuario.username, password="incorreta-ficticia")
    request = Mock()
    request.app.state.dummy_hash = "hash-ficticio"
    response = Response()
    settings = get_settings()
    cadastro = {usuario.username: usuario}
    with patch("app.routes.auth.verificar_senha", return_value=False) as verificar:
        with patch("app.routes.auth.resposta_token") as emitir:
            with pytest.raises(HTTPException) as erro:
                login(form, request, response, settings, cadastro)
    assert erro.value.status_code == 401
    verificar.assert_called_once()
    emitir.assert_not_called()


@pytest.mark.parametrize("scope,esperado", [("disponibilidade:ler", True), ("", False),
                                           ("consultas:escrever", False)])
def test_scope_m2m_nao_herda_privilegios_humanos(scope, esperado):
    from fastapi.security import SecurityScopes
    from app.auth.m2m import laboratorio

    request = Mock()
    claims = {"scope": scope}
    request.state.laboratorio = claims
    scopes = SecurityScopes(scopes=["disponibilidade:ler"])
    if esperado:
        assert laboratorio(scopes, request, None) == claims
    else:
        with pytest.raises(HTTPException) as erro:
            laboratorio(scopes, request, None)
        assert erro.value.status_code == 403
