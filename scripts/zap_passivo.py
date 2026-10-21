"""Tráfego fictício pelo proxy ZAP; não inicia spider nem scan ativo."""
import argparse
import json
import os
from pathlib import Path
import re
from secrets import token_urlsafe
import subprocess
import sys
import tempfile
import time

import httpx
from app.auth.passwords import gerar_hash

ROOT = Path(__file__).resolve().parents[1]
TARGET = "http://127.0.0.1:8001"
ZAP = "http://127.0.0.1:8090"
CONSULTAS_PATH = "/consultas"
BEARER_PREFIX = "Bearer "


def gerar_trafego(password: str, mfa: str, secrets: list[str]):
    traffic = []
    with httpx.Client(base_url=TARGET, proxy=ZAP, trust_env=False, timeout=20) as client:
        def request(method, path, expected, **kwargs):
            response = client.request(method, path, **kwargs)
            traffic.append({"method": method, "path": path, "status": response.status_code,
                            "expected": expected,
                            "headers": {k: response.headers[k] for k in (
                                "cache-control", "content-security-policy", "x-frame-options",
                                "x-content-type-options") if k in response.headers}})
            if response.status_code != expected:
                raise RuntimeError(f"Resposta inesperada: {method} {path}: {response.status_code}")
            return response

        def login(username, expected=200):
            response = request("POST", "/auth/token", expected, data={
                "grant_type": "password", "username": username, "password": password})
            key = "access_token" if expected == 200 else "challenge_id"
            value = response.json()[key]
            secrets.append(value)
            return value

        request("GET", "/", 200)
        request("GET", "/openapi.json", 200)
        request("GET", "/docs", 200)
        request("GET", CONSULTAS_PATH, 401)
        bearer = {"Authorization": BEARER_PREFIX + login("profissional1")}
        payload = {"paciente_id": 1, "profissional_id": 1,
                   "data_hora": "2026-10-20T09:00:00", "motivo": "Rotina fictícia",
                   "observacoes_internas": "Nota interna fictícia"}
        created = request("POST", CONSULTAS_PATH, 201, json=payload, headers=bearer)
        path = "/consultas/" + str(created.json()["id"])
        request("GET", CONSULTAS_PATH, 200, headers=bearer)
        request("GET", path, 200, headers=bearer)
        request("PATCH", path, 200, json={"motivo": "Revisão fictícia"}, headers=bearer)
        request("POST", CONSULTAS_PATH, 422, json={**payload, "papel": "administrador"}, headers=bearer)
        request("POST", CONSULTAS_PATH, 403, json={**payload, "paciente_id": 3,
                "profissional_id": 2}, headers=bearer)
        request("GET", "/admin/status", 403, headers=bearer)
        recepcao = {"Authorization": BEARER_PREFIX + login("recepcao")}
        request("POST", "/auth/agenda-session", 204, headers=recepcao)
        cookie = client.cookies.get("agenda_session")
        if cookie is None:
            raise RuntimeError("Sessão de agenda não foi emitida")
        secrets.append(cookie)
        request("GET", "/agenda?dia=2026-10-20", 200)
        request("DELETE", "/auth/agenda-session", 204, headers=recepcao)
        challenge = login("admin", 202)
        admin = request("POST", "/auth/mfa", 200, json={"challenge_id": challenge, "code": mfa})
        token = admin.json()["access_token"]
        secrets.append(token)
        request("GET", "/admin/status", 200, headers={"Authorization": BEARER_PREFIX + token})
        machine = request("POST", "/auth/m2m/token", 200, auth=("laboratorio_parceiro", password),
                          data={"grant_type": "client_credentials", "scope": "disponibilidade:ler"})
        token = machine.json()["access_token"]
        secrets.append(token)
        lab = {"Authorization": BEARER_PREFIX + token}
        free = "/disponibilidade?dia=2026-10-20&profissional_id=1"
        request("GET", free, 200, headers=lab)
        request("GET", free, 401, headers=bearer)
        request("GET", CONSULTAS_PATH, 401, headers=lab)
        request("DELETE", path, 204, headers=bearer)
        request("GET", path, 404, headers=bearer)
    return traffic


def executar(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    secrets = []

    def sanitizar(texto):
        for secret in sorted(secrets, key=len, reverse=True):
            texto = texto.replace(secret, "[REMOVIDO]")
        return re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT-REMOVIDO]", texto)

    with httpx.Client(base_url=ZAP, trust_env=False, timeout=30) as api:
        def zap(component, kind, action, **params):
            response = api.get(f"/JSON/{component}/{kind}/{action}/", params=params)
            response.raise_for_status()
            result = response.json()
            if "code" in result:
                raise RuntimeError(f"ZAP: {result}")
            return result

        version = zap("core", "view", "version")
        zap("core", "action", "newSession", name="", overwrite="true")
        zap("core", "action", "setMode", mode="safe")
        zap("ascan", "action", "disableAllScanners")
        zap("pscan", "action", "enableAllScanners")
        with tempfile.TemporaryDirectory(prefix="at-capstone-") as temp:
            work = Path(temp)
            password = token_urlsafe(20)
            mfa = "123456"
            jwt_secret = token_urlsafe(48)
            hashed = gerar_hash(password, rounds=4)
            secrets.extend([password, jwt_secret, hashed])
            users = work / "usuarios.json"
            users.write_text(json.dumps([
                {"username": name, "papel": role, "profissional_id": prof, "senha_hash": hashed}
                for name, role, prof in [("profissional1", "profissional", 1),
                                         ("recepcao", "recepcionista", None),
                                         ("admin", "administrador", None)]
            ]))
            env = {**os.environ, "JWT_SECRET": jwt_secret, "MFA_SIMULATED_CODE": mfa,
                   "USERS_FILE": str(users), "DATABASE_URL": "sqlite:///" + str(work / "scan.db"),
                   "AGENDA_COOKIE_SECURE": "false", "M2M_CLIENT_ID": "laboratorio_parceiro",
                   "M2M_CLIENT_SECRET_HASH": hashed, "LOGIN_RATE_LIMIT": "5", "GENERAL_RATE_LIMIT": "60"}
            with (output / "uvicorn.log").open("w") as log:
                process = subprocess.Popen([
                    sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                    "--port", "8001", "--no-access-log", "--no-server-header"],
                    cwd=ROOT, env=env, stdout=log, stderr=log)
                try:
                    with httpx.Client(base_url=TARGET, trust_env=False, timeout=10) as direct:
                        for _ in range(100):
                            if process.poll() is not None:
                                raise RuntimeError("Servidor não iniciou; consultar uvicorn.log")
                            try:
                                direct.get("/").raise_for_status()
                                break
                            except httpx.ConnectError:
                                time.sleep(0.1)
                        else:
                            raise TimeoutError("Servidor não iniciou no prazo")
                    traffic = gerar_trafego(password, mfa, secrets)
                    (output / "trafego.json").write_text(json.dumps(traffic, ensure_ascii=False, indent=2))
                    with httpx.Client(base_url=TARGET, trust_env=False) as direct:
                        (output / "openapi.json").write_text(json.dumps(direct.get("/openapi.json").json(),
                                                                       ensure_ascii=False, indent=2))
                    for _ in range(120):
                        if zap("pscan", "view", "recordsToScan")["recordsToScan"] == "0":
                            break
                        time.sleep(1)
                    else:
                        raise TimeoutError("Fila passiva não foi esvaziada")
                    # Dá tempo para a última mensagem já retirada da fila terminar.
                    time.sleep(2)
                    alerts = zap("core", "view", "alerts", baseurl=TARGET, start=0, count=1000)
                    (output / "alertas.json").write_text(sanitizar(json.dumps(alerts, ensure_ascii=False, indent=2)))
                    report = api.get("/OTHER/core/other/htmlreport/")
                    report.raise_for_status()
                    (output / "zap.html").write_text(sanitizar(report.text))
                    metadata = {"version": version["version"], "mode": zap("core", "view", "mode"),
                                "target": TARGET, "proxy": ZAP, "active_scan": False, "spider": False,
                                "recordsToScan": zap("pscan", "view", "recordsToScan"),
                                "messages": len(traffic), "alert_instances": len(alerts["alerts"]),
                                "temporary_database": True, "transport": "HTTP loopback; sem TLS real",
                                "cookie_secure": False}
                    (output / "execucao.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
                    print(json.dumps(metadata, ensure_ascii=False))
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    executar(parser.parse_args().output)
