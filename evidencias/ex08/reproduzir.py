"""Revisão exploratória isolada: histórico real, estado atual e experimento didático."""
import argparse
import html
import json
import os
import platform
import subprocess
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from typing import Annotated

ROOT = Path(__file__).resolve().parents[2]
DESTINO = Path(__file__).resolve().parent
CONSULTAS = "/consultas"
LOGIN = "/auth/token"
HEADERS = ["x-frame-options", "x-content-type-options", "strict-transport-security", "content-security-policy"]


def registrar(registros, cenario, response, esperado, *, corpo=None):
    assert response.status_code == esperado, cenario
    if corpo is None:
        corpo = response.json()
    registros.append({"cenario": cenario, "metodo": response.request.method,
        "url": response.request.url.path, "status": response.status_code, "corpo": corpo})


def payload(paciente, profissional, motivo):
    return {"paciente_id": paciente, "profissional_id": profissional,
            "data_hora": "2026-10-15T10:00:00", "motivo": motivo}


def historico(codigo):
    sys.path.insert(0, str(codigo))
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.memoria import reset_banco
    registros = []
    reset_banco()
    try:
        with TestClient(app) as client:
            for paciente in [1, 2]:
                resposta = client.post(CONSULTAS, json=payload(paciente, paciente, f"Registro fictício paciente {paciente}"))
                assert resposta.status_code == 201
            registrar(registros, "Histórico real: leitura do recurso 1 sem identidade", client.get(CONSULTAS + "/1"), 200)
            registrar(registros, "Histórico real: alterar apenas ID permite ler paciente 2 sem identidade", client.get(CONSULTAS + "/2"), 200)
            registrar(registros, "Histórico real: mutação do recurso 2 sem identidade", client.patch(CONSULTAS + "/2", json={"motivo": "Alteração indevida fictícia"}), 200)
    finally:
        reset_banco()
    return {"natureza": "código histórico real; sem autenticação, não é paciente autenticado", "casos": registros}


def atual(codigo=None):
    sys.path.insert(0, str(codigo or ROOT))
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth.passwords import gerar_hash
    from app.database.memoria import reset_banco
    from app.settings import get_settings
    registros = []
    names = ["JWT_SECRET", "MFA_SIMULATED_CODE", "USERS_FILE", "M2M_CLIENT_SECRET_HASH"]
    anteriores = {name: os.environ.get(name) for name in names}
    try:
        with TemporaryDirectory() as temp:
            senha = token_urlsafe(24)
            senha_invalida = senha + "-incorreta"
            cadastro = Path(temp) / "usuarios.json"
            senha_hash = gerar_hash(senha)
            cadastro.write_text(json.dumps([
                {"username": name, "papel": papel, "profissional_id": prof, "senha_hash": senha_hash}
                for name, papel, prof in [("profissional1", "profissional", 1), ("profissional2", "profissional", 2), ("recepcao", "recepcionista", None)]
            ]))
            os.environ.update(JWT_SECRET=token_urlsafe(48), MFA_SIMULATED_CODE=f"{int.from_bytes(os.urandom(4)) % 1000000:06d}",
                              USERS_FILE=str(cadastro), M2M_CLIENT_SECRET_HASH="")
            get_settings.cache_clear()
            reset_banco()
            with TestClient(app) as client:
                def login(username):
                    response = client.post(LOGIN, data={"grant_type": "password", "username": username, "password": senha})
                    assert response.status_code == 200
                    return {"Authorization": "Bearer " + response.json()["access_token"]}
                dono = login("profissional1")
                outro = login("profissional2")
                recepcao = login("recepcao")
                criada = client.post(CONSULTAS, headers=dono, json=payload(1, 1, "Dado clínico fictício protegido"))
                assert criada.status_code == 201
                alvo = CONSULTAS + "/1"
                registrar(registros, "Atual: proprietário autorizado lê", client.get(alvo, headers=dono), 200)
                registrar(registros, "Atual: outra identidade não lê ID conhecido", client.get(alvo, headers=outro), 404)
                registrar(registros, "Atual: outra identidade não altera", client.patch(alvo, headers=outro, json={"motivo": "Alteração indevida fictícia"}), 404)
                registrar(registros, "Atual: outra identidade não remove", client.delete(alvo, headers=outro), 404)
                registrar(registros, "Atual: anônimo não lê", client.get(alvo), 401)
                assert client.get(alvo, headers=dono).json() == criada.json()
                for i in range(20):
                    resposta = client.post(LOGIN, data={"grant_type": "password", "username": "profissional1", "password": senha_invalida})
                    registrar(registros, f"VUL-003: tentativa inválida {i + 1}/20 sem throttling", resposta, 401)
                    assert "retry-after" not in resposta.headers
                resposta = client.post(LOGIN, data={"grant_type": "password", "username": "profissional1", "password": senha})
                registrar(registros, "VUL-003: login correto após 20 erros não exige espera", resposta, 200, corpo="[token omitido; senha correta conhecida, não descoberta]")
                pagina = client.get("/agenda?dia=2026-10-15", headers=recepcao)
                assert pagina.status_code == 200
                ausencia = {header: pagina.headers.get(header) for header in HEADERS}
                assert all(value is None for value in ausencia.values())
                registrar(registros, "VUL-002: HTML autenticado sem headers de proteção", pagina, 200, corpo={"headers": ausencia, "html": "[HTML mínimo; conteúdo omitido]"})
                erro = client.get(alvo)
                registrar(registros, "VUL-002: headers também ausentes no erro", erro, 401,
                          corpo={"headers": {name: erro.headers.get(name) for name in HEADERS}})
                extra = {**payload(1, 1, "Entrada fictícia"), "papel": "administrador"}
                response = client.post(CONSULTAS, headers=dono, json=extra)
                assert response.status_code == 201
                assert "papel" not in response.json()
                registrar(registros, "OBS-001: campo extra ignorado; não promove identidade", response, 201)
                assert client.get("/admin/status", headers=dono).status_code == 403
                attack = "<script>alert(1)</script>"
                assert client.patch(alvo, headers=dono, json={"status": attack}).status_code == 200
                pagina = client.get("/agenda?dia=2026-10-15", headers=recepcao)
                assert pagina.status_code == 200
                assert attack not in pagina.text
                assert "&lt;script&gt;" in pagina.text
                registrar(registros, "OBS-002: payload persistido é escapado; não é XSS explorado", pagina, 200, corpo={"payload": attack, "exibicao_escapada": True})
    finally:
        for name, value in anteriores.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        get_settings.cache_clear()
        reset_banco()
    return {"natureza": "aplicação atual; dados/segredos fictícios efêmeros; sem correção neste exercício", "casos": registros}


def didatico():
    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.testclient import TestClient
    import jwt
    app = FastAPI(title="Experimento didático isolado de BOLA; não integra a aplicação")
    key = token_urlsafe(48)
    bearer = HTTPBearer()
    registros_ficticios = {1: {"id": 1, "paciente_id": 1, "resumo_clinico": "Relato fictício A"},
                          2: {"id": 2, "paciente_id": 2, "resumo_clinico": "Relato fictício B"}}

    def paciente(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
        try:
            return jwt.decode(credentials.credentials, key, algorithms=["HS256"], audience="experimento-pacientes")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Identidade fictícia inválida.") from None

    @app.get("/experimento/consultas/{consulta_id}", responses={404: {"description": "Consulta fictícia ausente."}})
    def consulta_sem_ownership(consulta_id: int, _identidade: Annotated[dict, Depends(paciente)]):
        if consulta_id not in registros_ficticios:
            raise HTTPException(404, "Consulta fictícia ausente.")
        # Falha didática: autenticação existe, mas não compara o paciente do alvo.
        return registros_ficticios[consulta_id]

    resultados = []
    now = datetime.now(timezone.utc)
    with TestClient(app) as client:
        for paciente_id in [1, 2]:
            token = jwt.encode({"sub": f"paciente{paciente_id}", "paciente_id": paciente_id,
                "aud": "experimento-pacientes", "exp": now + timedelta(minutes=5)}, key, algorithm="HS256")
            headers = {"Authorization": "Bearer " + token}
            registrar(resultados, f"Didático: paciente {paciente_id} lê registro próprio", client.get(f"/experimento/consultas/{paciente_id}", headers=headers), 200)
            alvo = 2 if paciente_id == 1 else 1
            registrar(resultados, f"Didático: mesmo token do paciente {paciente_id}, somente ID trocado para {alvo}", client.get(f"/experimento/consultas/{alvo}", headers=headers), 200)
    return {"natureza": "experimento criado para ensino; não é finding no código atual nem histórico; aceitação acadêmica pendente", "casos": resultados}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--etapa", choices=["historico", "atual", "didatico"])
    parser.add_argument("--codigo", type=Path)
    args = parser.parse_args()
    if args.etapa:
        if args.etapa == "historico":
            resultado = historico(args.codigo)
        elif args.etapa == "atual":
            resultado = atual(args.codigo)
        else:
            resultado = didatico()
        (DESTINO / f"{args.etapa}.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n")
        print(f"{args.etapa}: {len(resultado['casos'])} observações verificadas; segredos omitidos.")
        return
    manifesto = json.loads((DESTINO / "manifesto.json").read_text())
    with TemporaryDirectory() as temp:
        for etapa in ["historico", "atual", "didatico"]:
            codigo = Path(temp) / etapa
            for fonte in manifesto["arquivos"]:
                if not fonte["snapshot"].startswith(f"snapshots/{etapa}/"):
                    continue
                data = (DESTINO / fonte["snapshot"]).read_bytes()
                if hashlib.sha256(data).hexdigest() != fonte["sha256"]:
                    raise ValueError("Snapshot não corresponde ao SHA-256 registrado.")
                target = codigo / fonte["origem"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--etapa", etapa,
                            "--codigo", str(codigo)], cwd=ROOT, check=True)
    ambiente = {"python": platform.python_version(), "pacotes": {name: version(name) for name in ["fastapi", "PyJWT", "bcrypt", "pytest", "httpx"]}}
    (DESTINO / "ambiente.json").write_text(json.dumps(ambiente, indent=2) + "\n")
    documentos = []
    for etapa in ["historico", "atual", "didatico"]:
        obj = json.loads((DESTINO / f"{etapa}.json").read_text())
        documentos.append(f"<h2>{etapa}</h2><p>{html.escape(obj['natureza'])}</p><pre>{html.escape(json.dumps(obj['casos'], ensure_ascii=False, indent=2))}</pre>")
    (DESTINO / "revisao.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Revisão manual — Ex. 8</title><style>body{font-family:sans-serif;margin:24px}pre{white-space:pre-wrap}</style><h1>Revisão manual — evidências HTTP</h1>' + "".join(documentos) + "</html>\n")

if __name__ == "__main__":
    main()
