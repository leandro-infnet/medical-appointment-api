"""Gera evidências HTTP isoladas com dados fictícios, sem servidor externo.

Executar na raiz: .venv/bin/python evidencias/ex02/reproduzir.py
"""

import json
import sys
from pathlib import Path

# Permite executar o arquivo diretamente a partir da instalação ou do checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.database.consultas import obter_consulta_por_id
from app.database.memoria import reset_banco
from app.main import app


def main():
    pasta = Path(__file__).resolve().parent
    payload = {
        "paciente_id": 1,
        "profissional_id": 2,
        "data_hora": "2026-10-03T09:00:00",
        "motivo": "Informacao clinica ficticia confidencial",
        "observacoes_internas": "Nota interna ficticia restrita",
    }
    ataque = {"status": "<script>alert(1)</script>"}
    reset_banco()
    try:
        with TestClient(app) as client:
            criada = client.post("/consultas", json=payload)
            assert criada.status_code == 201
            consulta_id = criada.json()["id"]
            detalhe = client.get(f"/consultas/{consulta_id}")
            lista = client.get("/consultas")
            alterada = client.patch(f"/consultas/{consulta_id}", json=ataque)
            assert alterada.status_code == 200
            armazenada = obter_consulta_por_id(consulta_id)
            assert armazenada is not None, "A consulta criada deve existir no armazenamento."
            assert armazenada.status == ataque["status"]
            pagina = client.get("/agenda?dia=2026-10-03")
            assert pagina.status_code == 200
            assert "&lt;script&gt;alert(1)&lt;/script&gt;" in pagina.text
            assert ataque["status"] not in pagina.text
            assert payload["observacoes_internas"] not in pagina.text
            assert payload["motivo"] not in pagina.text
            evidencias = {
                "origem": "HTTP em processo via FastAPI TestClient; memória isolada",
                "POST /consultas": {"status": criada.status_code, "json": criada.json()},
                "GET /consultas/1": {"status": detalhe.status_code, "json": detalhe.json()},
                "GET /consultas": {"status": lista.status_code, "json": lista.json()},
                "PATCH /consultas/1": {"status": alterada.status_code, "json": alterada.json()},
                "campos_armazenados": sorted(armazenada.model_dump()),
                "GET /agenda?dia=2026-10-03": {
                    "status": pagina.status_code,
                    "content_type": pagina.headers["content-type"],
                    "template": pagina.template.name,
                    "campos_no_contexto": sorted(pagina.context["consultas"][0]),
                    "payload_armazenado": armazenada.status,
                    "saida_escapada": "&lt;script&gt;alert(1)&lt;/script&gt;",
                },
            }
            pasta.joinpath("respostas_http.json").write_text(
                json.dumps(evidencias, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            pasta.joinpath("payloads.json").write_text(
                json.dumps({"criacao": payload, "ataque_didatico": ataque},
                           ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            pasta.joinpath("agenda_xss.html").write_text(pagina.text, encoding="utf-8")
            pasta.joinpath("agenda_vazia.html").write_text(
                client.get("/agenda?dia=2026-10-04").text, encoding="utf-8",
            )
        print("Evidências JSON e HTML gravadas em evidencias/ex02; memória descartada.")
    finally:
        reset_banco()


if __name__ == "__main__":
    main()
