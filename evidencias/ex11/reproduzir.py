"""Migração SQLite com dados fictícios e reinício em dois processos distintos."""
import json
import os
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from secrets import randbelow, token_urlsafe
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, select
from app.auth.passwords import gerar_hash
from app.main import app
from app.models.tabelas import ConsultaTabela

DESTINO = Path(__file__).resolve().parent
CONSULTAS = "/consultas"
LOGIN = "/auth/token"
PAYLOAD_SQL = "x'); DROP TABLE consultas; --"
PAYLOAD = {"paciente_id": 1, "profissional_id": 1,
           "data_hora": "2026-10-15T09:00:00", "motivo": PAYLOAD_SQL,
           "observacoes_internas": "Nota fictícia não pública"}


def registrar(casos, nome, response, expected):
    assert response.status_code == expected, nome
    casos.append({"cenario": nome, "status": response.status_code})


def executar_etapa(etapa: str, destino: Path):
    casos = []
    sqls = []
    with TestClient(app) as client:
        def login(nome):
            resposta = client.post(LOGIN, data={"grant_type": "password", "username": nome,
                "password": os.environ["DEMO_PASSWORD"]})
            assert resposta.status_code == 200
            return {"Authorization": "Bearer " + resposta.json()["access_token"]}
        dono = login("profissional1")
        outro = login("profissional2")
        recepcao = login("recepcao")
        def capturar(_connection, _cursor, statement, parameters, _context, _executemany):
            if statement.startswith("INSERT INTO consultas"):
                assert PAYLOAD_SQL not in statement
                assert PAYLOAD_SQL in parameters
                sqls.append({"sql": statement, "payload_e_parametro": True,
                             "valores": "omitidos para minimizar dados"})
        if etapa == "criar":
            event.listen(app.state.engine, "before_cursor_execute", capturar)
            try:
                registrar(casos, "Criar com literal SQL como dado", client.post(CONSULTAS, headers=dono, json=PAYLOAD), 201)
            finally:
                event.remove(app.state.engine, "before_cursor_execute", capturar)
            assert sqls
        else:
            resposta = client.get(CONSULTAS + "/1", headers=dono)
            registrar(casos, "Consulta preservada em novo processo", resposta, 200)
            assert resposta.json()["motivo"] == PAYLOAD_SQL
            assert resposta.json()["data_hora"] == "2026-10-15T09:00:00-03:00"
            assert "observacoes_internas" not in resposta.json()
            registrar(casos, "Ownership preservado no banco", client.get(CONSULTAS + "/1", headers=outro), 404)
            registrar(casos, "ID com operador SQL rejeitado", client.get(CONSULTAS + "/1 OR 1=1", headers=dono), 422)
            registrar(casos, "Filtro com operador SQL rejeitado", client.get(CONSULTAS, headers=dono,
                params={"paciente_id": "1 OR 1=1"}), 422)
            registrar(casos, "Sobreposição bloqueada", client.post(CONSULTAS, headers=dono,
                json={**PAYLOAD, "data_hora": "2026-10-15T09:15:00"}), 409)
            pagina = client.get("/agenda?dia=2026-10-15", headers=recepcao)
            registrar(casos, "Agenda lê o banco com projeção mínima", pagina, 200)
            assert PAYLOAD_SQL not in pagina.text
            token = client.post("/auth/m2m/token", data={"grant_type": "client_credentials"},
                auth=("laboratorio_parceiro", os.environ["DEMO_PASSWORD"]))
            assert token.status_code == 200
            disponibilidade = client.get("/disponibilidade", params={"dia": "2026-10-15", "profissional_id": 1},
                headers={"Authorization": "Bearer " + token.json()["access_token"]})
            registrar(casos, "M2M usa a mesma persistência", disponibilidade, 200)
            assert len(disponibilidade.json()["intervalos"]) == 19
            assert "paciente" not in disponibilidade.text
            registrar(casos, "Atualizar no banco", client.patch(CONSULTAS + "/1", headers=dono,
                json={"status": "cancelada"}), 200)
            registrar(casos, "Cancelamento libera horário", client.post(CONSULTAS, headers=dono,
                json={**PAYLOAD, "data_hora": "2026-10-15T09:15:00"}), 201)
            registrar(casos, "Reativação conflitante bloqueada", client.patch(CONSULTAS + "/1", headers=dono,
                json={"status": "agendada"}), 409)
            assert client.get(CONSULTAS + "/1", headers=dono).json()["status"] == "cancelada"
            registrar(casos, "Excluir no banco", client.delete(CONSULTAS + "/2", headers=dono), 204)
            registrar(casos, "Exclusão persistida", client.get(CONSULTAS + "/2", headers=dono), 404)
        with Session(app.state.engine) as session:
            assert len(session.exec(select(ConsultaTabela)).all()) == 1
    destino.write_text(json.dumps({"etapa": etapa, "casos": casos, "queries": sqls}, ensure_ascii=False, indent=2) + "\n")


def main():
    with TemporaryDirectory() as temp:
        base = Path(temp)
        senha = token_urlsafe(24)
        senha_hash = gerar_hash(senha)
        usuarios = base / "usuarios.json"
        usuarios.write_text(json.dumps([
            {"username": nome, "papel": papel, "profissional_id": profissional, "senha_hash": senha_hash}
            for nome, papel, profissional in [("profissional1", "profissional", 1),
                ("profissional2", "profissional", 2), ("recepcao", "recepcionista", None)]
        ]))
        ambiente = {**os.environ, "DATABASE_URL": "sqlite:///" + str(base / "consultas.db"),
            "JWT_SECRET": token_urlsafe(48), "MFA_SIMULATED_CODE": f"{randbelow(1000000):06d}",
            "USERS_FILE": str(usuarios), "M2M_CLIENT_SECRET_HASH": senha_hash,
            "M2M_CLIENT_ID": "laboratorio_parceiro", "DEMO_PASSWORD": senha,
            "CORS_ORIGINS": '["http://localhost:5173"]', "LOGIN_RATE_LIMIT": "5", "GENERAL_RATE_LIMIT": "60"}
        etapas = []
        for etapa in ("criar", "ler"):
            arquivo = base / (etapa + ".json")
            subprocess.run([sys.executable, str(Path(__file__).resolve()), etapa, str(arquivo)],
                           env=ambiente, cwd=ROOT, check=True)
            etapas.append(json.loads(arquivo.read_text()))
        resultado = {"etapas_em_processos_distintos": etapas,
                     "limites": ["SQLite local com dados fictícios em diretório temporário.",
                                "Nenhum banco, segredo, token ou cadastro é copiado para a evidência.",
                                "Reinício demonstrado com TestClient em processos distintos, sem deploy."]}
        (DESTINO / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    versoes = {"python": platform.python_version(), "sqlite": __import__("sqlite3").sqlite_version,
              "pacotes": {nome: version(nome) for nome in ("sqlmodel", "SQLAlchemy", "pydantic", "fastapi", "pytest")}}
    (DESTINO / "ambiente.json").write_text(json.dumps(versoes, indent=2) + "\n")
    print(f"{sum(len(etapa['casos']) for etapa in etapas)} observações HTTP verificadas em dois processos distintos.")
    print("Query INSERT com parâmetros vinculados; bancos temporários removidos; segredos omitidos.")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        executar_etapa(sys.argv[1], Path(sys.argv[2]))
    else:
        main()
