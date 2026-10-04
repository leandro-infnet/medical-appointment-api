"""Persistência real SQLite, parâmetros, integridade e concorrência de agenda."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
import sqlite3
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.main import app
from app.models.tabelas import ConsultaTabela, PacienteTabela
from app.settings import Settings, get_settings

CONSULTAS = "/consultas"
PAYLOAD = {"paciente_id": 1, "profissional_id": 1,
           "data_hora": "2026-10-15T09:00:00", "motivo": "Consulta fictícia"}


def test_persistencia_apos_novo_lifespan_e_seed_idempotente():
    for primeira in (True, False):
        with TestClient(app) as client:
            token = client.post("/auth/token", data={"grant_type": "password", "username": "profissional1",
                "password": "senha-ficticia-testes"}).json()["access_token"]
            client.headers.update({"Authorization": "Bearer " + token})
            if primeira:
                assert client.post(CONSULTAS, json=PAYLOAD).status_code == 201
            else:
                resposta = client.get(CONSULTAS)
                assert resposta.status_code == 200
                assert len(resposta.json()) == 1
                assert resposta.json()[0]["id"] == 1
            with Session(app.state.engine) as session:
                assert len(session.exec(select(PacienteTabela)).all()) == 2


def test_sql_injection_e_parametros_vinculados(client):
    payload = "x'); DROP TABLE consultas; --"
    observados = []
    def registrar(_connection, _cursor, statement, parameters, _context, _executemany):
        observados.append((statement, parameters))
    event.listen(app.state.engine, "before_cursor_execute", registrar)
    try:
        criada = client.post(CONSULTAS, json={**PAYLOAD, "motivo": payload})
        assert criada.status_code == 201
        assert client.get("/consultas/1").json()["motivo"] == payload
        assert client.get(CONSULTAS, params={"paciente_id": "1 OR 1=1"}).status_code == 422
        assert client.get("/consultas/1 OR 1=1").status_code == 422
        assert client.patch("/consultas/1", json={"motivo": payload + " update"}).status_code == 200
        assert len(client.get(CONSULTAS).json()) == 1
    finally:
        event.remove(app.state.engine, "before_cursor_execute", registrar)
    insert = next((sql, values) for sql, values in observados if sql.startswith("INSERT INTO consultas"))
    assert payload not in insert[0]
    assert "?" in insert[0]
    assert payload in insert[1]


@pytest.mark.parametrize("changes", [{"paciente_id": 999}, {"profissional_id": 999},
    {"status": "invalido"}, {"motivo": "x"}, {"observacoes_internas": "x" * 501}])
def test_constraints_e_rollback_sem_registro_parcial(db_session, changes):
    dados = {**PAYLOAD, "data_hora": datetime(2026, 10, 15, 12), **changes}
    registro = ConsultaTabela(**dados)
    db_session.add(registro)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.exec(select(ConsultaTabela)).all() == []
    assert db_session.get(PacienteTabela, 1) is not None


def test_conflito_atualizacao_rollback_e_cancelamento(client):
    primeira = client.post(CONSULTAS, json=PAYLOAD)
    assert primeira.status_code == 201
    assert client.post(CONSULTAS, json={**PAYLOAD, "data_hora": "2026-10-15T09:15:00"}).status_code == 409
    segunda = client.post(CONSULTAS, json={**PAYLOAD, "data_hora": "2026-10-15T09:30:00"})
    assert segunda.status_code == 201
    path = f"/consultas/{segunda.json()['id']}"
    assert client.patch(path, json={"data_hora": "2026-10-15T09:15:00", "motivo": "Não deve salvar"}).status_code == 409
    assert client.get(path).json() == segunda.json()
    assert client.patch("/consultas/1", json={"status": "cancelada"}).status_code == 200
    assert client.patch(path, json={"data_hora": "2026-10-15T09:15:00"}).status_code == 200
    assert client.patch("/consultas/1", json={"status": "agendada"}).status_code == 409
    assert client.get("/consultas/1").json()["status"] == "cancelada"
    assert client.delete(path).status_code == 204
    assert client.patch("/consultas/1", json={"status": "realizada"}).status_code == 200


def test_conflito_equivalente_utc_e_isolamento_por_profissional(client, autenticar):
    assert client.post(CONSULTAS, json=PAYLOAD).status_code == 201
    assert client.post(CONSULTAS, json={**PAYLOAD, "data_hora": "2026-10-15T12:15:00Z"}).status_code == 409
    outro = autenticar("profissional2")
    assert client.post(CONSULTAS, headers=outro, json={**PAYLOAD,
        "paciente_id": 2, "profissional_id": 2}).status_code == 201


@pytest.mark.parametrize("operacao", ["criar", "atualizar"])
def test_concorrencia_real_sqlite_um_intervalo_um_vencedor(client, operacao):
    if operacao == "atualizar":
        for horario in ("10:00", "11:00"):
            assert client.post(CONSULTAS, json={**PAYLOAD, "data_hora": f"2026-10-15T{horario}:00"}).status_code == 201
    barreira = Barrier(2)
    def disputar(index):
        barreira.wait(timeout=5)
        horario = f"2026-10-15T09:{index * 15:02d}:00"
        if operacao == "criar":
            return client.post(CONSULTAS, json={**PAYLOAD, "data_hora": horario}).status_code
        return client.patch(f"/consultas/{index + 1}", json={"data_hora": horario}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(disputar, (0, 1)))
    assert sorted(resultados) == ([201, 409] if operacao == "criar" else [200, 409])
    with Session(app.state.engine) as session:
        linhas = session.exec(select(ConsultaTabela).where(
            ConsultaTabela.data_hora >= datetime(2026, 10, 15, 12),
            ConsultaTabela.data_hora < datetime(2026, 10, 15, 12, 30))).all()
        assert len(linhas) == 1


def test_banco_ocupado_retorna_503_sem_expor_sql_ou_configuracao(client):
    # Timeout zero só neste teste, sem aguardar os cinco segundos de produção.
    with app.state.engine.connect() as conexao:
        conexao.exec_driver_sql("PRAGMA busy_timeout=0")
    url = get_settings().database_url.get_secret_value()
    with sqlite3.connect(url.removeprefix("sqlite:///")) as lock:
        lock.execute("BEGIN IMMEDIATE")
        resposta = client.post(CONSULTAS, json=PAYLOAD)
        assert resposta.status_code == 503
        assert resposta.json() == {"detail": "Banco temporariamente ocupado. Tente novamente."}
        assert resposta.headers["retry-after"] == "5"
        lock.rollback()
    assert client.post(CONSULTAS, json=PAYLOAD).status_code == 201


@pytest.mark.parametrize("url", ["", "sqlite://", "sqlite:///:memory:",
    "postgresql://example.org/banco", "sqlite:///teste.db?mode=ro"])
def test_url_configurada_rejeita_banco_fora_do_contrato(url):
    segredo = SecretStr(url)
    settings = get_settings()
    with pytest.raises(ValidationError):
        Settings(database_url=segredo, jwt_secret=settings.jwt_secret,
                 mfa_simulated_code=settings.mfa_simulated_code)


def test_sessao_independente_por_requisicao_e_encerrada(client, monkeypatch):
    sessoes = []
    from app.database import session as modulo
    original = modulo.Session
    class SessaoMonitorada(original):
        def close(self):
            super().close()
            self.encerrada = True
    def criar(*args, **kwargs):
        sessao = SessaoMonitorada(*args, **kwargs)
        sessao.encerrada = False
        sessoes.append(sessao)
        return sessao
    monkeypatch.setattr(modulo, "Session", criar)
    assert client.get(CONSULTAS).status_code == 200
    assert client.get("/consultas/999").status_code == 404
    assert len(sessoes) == 2
    assert sessoes[0] is not sessoes[1]
    assert all(sessao.encerrada for sessao in sessoes)
