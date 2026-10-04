"""Correções HTTP reais e experimento SQL isolado, somente com dados fictícios."""
import html
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from secrets import randbelow, token_urlsafe
from tempfile import TemporaryDirectory
from typing import Annotated

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if len(sys.argv) == 3 and sys.argv[1] == "--baseline-m2m":
    sys.path.insert(0, sys.argv[2])

from fastapi.testclient import TestClient
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from app.auth.passwords import gerar_hash
from app.database.memoria import _consultas, _lock, reset_banco
from app.main import app
from app.settings import get_settings

DESTINO = Path(__file__).resolve().parent
CONSULTAS = "/consultas"
LOGIN = "/auth/token"
XSS = "<script>alert(1)</script>"
PAYLOAD = {"paciente_id": 1, "profissional_id": 1,
           "data_hora": "2026-10-15T10:00:00", "motivo": "Avaliação fictícia"}


def registrar(registros, nome, resposta, esperado):
    assert resposta.status_code == esperado, nome
    registros.append({"cenario": nome, "metodo": resposta.request.method,
                      "url": resposta.request.url.path, "status": resposta.status_code})


def verificar_sql():
    """DEMO-002: SQL vulnerável nunca é importado ou servido pela aplicação."""
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE consultas (id INTEGER PRIMARY KEY, paciente_id INTEGER)")
        connection.executemany("INSERT INTO consultas VALUES (?, ?)", [(1, 1), (2, 2)])
        ataque = "1 OR 1=1"
        # Concatenação intencional apenas no ANTES do experimento didático isolado.
        antes = connection.execute("SELECT id FROM consultas WHERE paciente_id = " + ataque).fetchall()
        depois = connection.execute("SELECT id FROM consultas WHERE paciente_id = ?", (ataque,)).fetchall()
        positivo = connection.execute("SELECT id FROM consultas WHERE paciente_id = ?", (1,)).fetchall()
        assert antes == [(1,), (2,)]
        assert depois == []
        assert positivo == [(1,)]
    return {"id": "DEMO-002", "natureza": "didático isolado; não é finding SQL da aplicação",
            "payload": ataque, "antes_ids": [row[0] for row in antes],
            "depois_ids": [], "controle_positivo_ids": [1],
            "correcao": "placeholder ? com valores separados do SQL",
            "limite": "Não demonstra migração SQLModel, ownership SQL ou aceitação acadêmica."}


def verificar_form_m2m(esperado):
    nomes = ("JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "M2M_CLIENT_SECRET_HASH", "M2M_CLIENT_ID")
    anteriores = {nome: os.environ.get(nome) for nome in nomes}
    registros = []
    try:
        with TemporaryDirectory() as temp:
            senha = token_urlsafe(24)
            usuarios = Path(temp) / "usuarios.json"
            usuarios.write_text("[]")
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE=f"{randbelow(1000000):06d}",
                              USERS_FILE=str(usuarios), M2M_CLIENT_SECRET_HASH=gerar_hash(senha),
                              M2M_CLIENT_ID="laboratorio_parceiro")
            get_settings.cache_clear()
            with TestClient(app) as client:
                for form, status, nome in [
                    ({"grant_type": "client_credentials"}, 200, "Controle positivo M2M"),
                    ({"grant_type": "client_credentials", "papel": "administrador"}, esperado, "Mesmo campo extra M2M"),
                ]:
                    resposta = client.post("/auth/m2m/token", data=form, auth=("laboratorio_parceiro", senha))
                    registrar(registros, nome, resposta, status)
    finally:
        for nome, valor in anteriores.items():
            if valor is None:
                os.environ.pop(nome, None)
            else:
                os.environ[nome] = valor
        get_settings.cache_clear()
    return registros


def verificar_m2m_antes():
    manifesto = json.loads((ROOT / "evidencias/ex08/manifesto.json").read_text())
    with TemporaryDirectory() as temp:
        for fonte in manifesto["arquivos"]:
            if not fonte["snapshot"].startswith("snapshots/atual/"):
                continue
            data = (ROOT / "evidencias/ex08" / fonte["snapshot"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != fonte["sha256"]:
                raise ValueError("Snapshot com SHA-256 divergente.")
            target = Path(temp) / fonte["origem"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--baseline-m2m", temp], check=True)
    return json.loads((DESTINO / "m2m-antes.json").read_text())


def verificar_http():
    nomes = ("JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "M2M_CLIENT_SECRET_HASH")
    anteriores = {nome: os.environ.get(nome) for nome in nomes}
    registros = []
    try:
        with TemporaryDirectory() as temp:
            senha = token_urlsafe(24)
            arquivo = Path(temp) / "usuarios.json"
            senha_hash = gerar_hash(senha)
            arquivo.write_text(json.dumps([
                {"username": nome, "papel": papel, "profissional_id": prof, "senha_hash": senha_hash}
                for nome, papel, prof in [("profissional1", "profissional", 1),
                                         ("profissional2", "profissional", 2),
                                         ("recepcao", "recepcionista", None)]
            ]))
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE=f"{randbelow(1000000):06d}",
                              USERS_FILE=str(arquivo), M2M_CLIENT_SECRET_HASH="")
            get_settings.cache_clear()
            reset_banco()
            with TestClient(app) as client:
                def login(nome):
                    resposta = client.post(LOGIN, data={"grant_type": "password", "username": nome,
                                                       "password": senha})
                    assert resposta.status_code == 200
                    return {"Authorization": "Bearer " + resposta.json()["access_token"]}
                dono, outro, recepcao = login("profissional1"), login("profissional2"), login("recepcao")
                criada = client.post(CONSULTAS, json=PAYLOAD, headers=dono)
                registrar(registros, "Controle positivo: criar", criada, 201)
                consulta_id = criada.json()["id"]
                path = f"{CONSULTAS}/{consulta_id}"
                registrar(registros, "OBS-001: mesmo papel extra agora rejeitado", client.post(
                    CONSULTAS, headers=dono, json={**PAYLOAD, "papel": "administrador"}), 422)
                registrar(registros, "Endpoint adicional PATCH: papel extra rejeitado", client.patch(
                    path, headers=dono, json={"papel": "administrador"}), 422)
                registrar(registros, "Endpoint adicional PATCH: troca de vínculo rejeitada", client.patch(
                    path, headers=dono, json={"paciente_id": 2}), 422)
                registrar(registros, "VUL-001: leitura anônima do mesmo ID bloqueada", client.get(path), 401)
                registrar(registros, "VUL-001: mutação anônima do mesmo ID bloqueada", client.patch(
                    path, json={"motivo": "Alteração indevida fictícia"}), 401)
                registrar(registros, "Ownership: outra identidade não lê", client.get(path, headers=outro), 404)
                registrar(registros, "Ownership: outra identidade não altera", client.patch(
                    path, headers=outro, json={"motivo": "Alteração indevida fictícia"}), 404)
                registrar(registros, "Ownership: outra identidade não remove", client.delete(path, headers=outro), 404)
                registrar(registros, "OBS-002: mesmo payload de status rejeitado", client.patch(
                    path, headers=dono, json={"status": XSS}), 422)
                assert client.get(path, headers=dono).json() == criada.json()
                for estado in ("agendada", "realizada", "cancelada"):
                    registrar(registros, f"Allowlist: {estado}", client.patch(
                        path, headers=dono, json={"status": estado}), 200)
                registrar(registros, "Regex: username com operador SQL rejeitado", client.post(
                    LOGIN, data={"grant_type": "password", "username": "x' OR '1'='1", "password": senha}), 422)
                registrar(registros, "Middleware: token adulterado", client.get(
                    path, headers={"Authorization": "Bearer invalido"}), 401)
                # Persistência de texto legado controlada só neste processo de teste.
                with _lock:
                    _consultas[consulta_id]["status"] = XSS
                pagina = client.get("/agenda?dia=2026-10-15", headers=recepcao)
                registrar(registros, "Saída: legado com mesmo payload continua escapado", pagina, 200)
                assert XSS not in pagina.text
                assert "&lt;script&gt;alert(1)&lt;/script&gt;" in pagina.text
                html_legado = "\n".join(line.rstrip() for line in pagina.text.splitlines()) + "\n"
                (DESTINO / "agenda-legado.html").write_text(html_legado)
    finally:
        for nome, valor in anteriores.items():
            if valor is None:
                os.environ.pop(nome, None)
            else:
                os.environ[nome] = valor
        get_settings.cache_clear()
        reset_banco()
    return registros


def verificar_pacientes_isolados():
    """Contraparte corrigida de DEMO-001; não cria papel ou portal no produto."""
    experimento = FastAPI(title="DEMO-001 corrigido; isolado")
    chave = token_urlsafe(48)
    bearer = HTTPBearer()
    consultas = {1: {"id": 1, "paciente_id": 1}, 2: {"id": 2, "paciente_id": 2}}

    def paciente(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
        try:
            return jwt.decode(credentials.credentials, chave, algorithms=["HS256"],
                              audience="experimento-pacientes", options={"require": ["sub", "exp", "aud", "paciente_id"]})
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Token fictício inválido.") from None

    @experimento.get("/experimento/consultas/{consulta_id}", responses={
        401: {"description": "Token inválido."}, 404: {"description": "Ausente ou não autorizado."}})
    def consulta(consulta_id: int, identidade: Annotated[dict, Depends(paciente)]):
        recurso = consultas.get(consulta_id)
        if recurso is None or recurso["paciente_id"] != identidade["paciente_id"]:
            raise HTTPException(404, "Consulta fictícia não encontrada.")
        return recurso

    registros = []
    with TestClient(experimento) as client:
        for paciente_id in (1, 2):
            token = jwt.encode({"sub": f"paciente{paciente_id}", "paciente_id": paciente_id,
                "aud": "experimento-pacientes", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                chave, algorithm="HS256")
            headers = {"Authorization": "Bearer " + token}
            registrar(registros, f"DEMO-001: paciente {paciente_id} lê próprio registro", client.get(
                f"/experimento/consultas/{paciente_id}", headers=headers), 200)
            alvo = 2 if paciente_id == 1 else 1
            registrar(registros, f"DEMO-001: somente ID trocado para {alvo}, mesmo token", client.get(
                f"/experimento/consultas/{alvo}", headers=headers), 404)
    return registros


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--baseline-m2m":
        antes = verificar_form_m2m(200)
        (DESTINO / "m2m-antes.json").write_text(json.dumps(antes, ensure_ascii=False, indent=2) + "\n")
        print("Baseline real M2M: controle positivo e campo extra ignorado verificados; tokens omitidos.")
        return
    http = verificar_http()
    sql = verificar_sql()
    pacientes = verificar_pacientes_isolados()
    m2m_antes = verificar_m2m_antes()
    m2m_depois = verificar_form_m2m(422)
    fontes = {}
    # Resultados anteriores preservados; não são novas execuções nesta etapa.
    for nome in ("historico", "atual", "didatico"):
        fontes[nome] = json.loads((ROOT / "evidencias/ex08" / f"{nome}.json").read_text())
    resultado = {"http_atual": http, "sql_isolado": sql, "pacientes_isolados_depois": pacientes,
                 "endpoint_adicional_m2m": {"antes": m2m_antes, "depois": m2m_depois},
                 "antes_preservado_ex08": fontes,
                 "limites": ["XSS real já escapava antes; não houve exploração demonstrada.",
                             "Paciente autenticado existe somente em experimento isolado.",
                             "SQLModel e persistência da aplicação permanecem para Ex. 11."]}
    (DESTINO / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    ambiente = {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                "pacotes": {nome: version(nome) for nome in ("fastapi", "pydantic", "PyJWT", "bcrypt", "pytest")}}
    (DESTINO / "ambiente.json").write_text(json.dumps(ambiente, indent=2) + "\n")
    (DESTINO / "comparacao.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<title>Ex. 9 — antes e depois</title><h1>Correções e limites da evidência</h1><pre>'
        + html.escape(json.dumps(resultado, ensure_ascii=False, indent=2)) + '</pre></html>\n')
    print(f"HTTP atual: {len(http)} observações verificadas; SQL isolado: ataque e controle positivo verificados.")
    print(f"Pacientes isolados: {len(pacientes)} observações verificadas; aceite acadêmico pendente.")
    print("Endpoint adicional M2M: 2 observações no baseline real e 2 depois da correção.")
    print("Dados fictícios; segredos omitidos; resultados anteriores apenas preservados.")


if __name__ == "__main__":
    main()
