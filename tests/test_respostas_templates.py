"""Contratos HTTP de saída e proteção da agenda do Exercício 2."""

from datetime import datetime
from html.parser import HTMLParser

import pytest

from app.database.consultas import FUSO_CLINICA, obter_consulta_por_id


class InspecionarHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.textos = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)

    def handle_data(self, data):
        self.textos.append(data)


def criar(client, horario="2026-10-03T09:00:00"):
    resposta = client.post("/consultas", json={
        "paciente_id": 1,
        "profissional_id": 2,
        "data_hora": horario,
        "motivo": "Informacao clinica ficticia confidencial",
        "observacoes_internas": "Nota interna ficticia restrita",
    })
    assert resposta.status_code == 201
    return resposta


def test_respostas_excluem_campos_internos_sem_apagar_armazenamento(client):
    criada = criar(client)
    consulta_id = criada.json()["id"]
    respostas = [
        criada.json(),
        client.get(f"/consultas/{consulta_id}").json(),
        client.get("/consultas").json()[0],
        client.patch(f"/consultas/{consulta_id}", json={
            "observacoes_internas": "Nota interna atualizada",
        }).json(),
    ]
    campos = {"id", "paciente_id", "profissional_id", "data_hora", "motivo", "status"}
    for resposta in respostas:
        assert set(resposta) == campos
    armazenada = obter_consulta_por_id(consulta_id)
    assert armazenada is not None
    assert armazenada.observacoes_internas == "Nota interna atualizada"
    assert armazenada.criado_em is not None
    assert armazenada.atualizado_em is not None


def test_agenda_filtra_dia_ordena_e_minimiza_contexto(client):
    criar(client, "2026-10-03T15:00:00")
    criar(client, "2026-10-03T09:00:00")
    criar(client, "2026-10-04T12:00:00")
    resposta = client.get("/agenda", params={"dia": "2026-10-03"})
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert resposta.template.name == "agenda.html"
    assert "<h1>Agenda da clínica</h1>" in resposta.text  # conteúdo herdado
    assert len(resposta.context["consultas"]) == 2
    assert resposta.text.index("09:00") < resposta.text.index("15:00")
    assert "12:00" not in resposta.text
    assert "Informacao clinica ficticia confidencial" not in resposta.text
    assert "Nota interna ficticia restrita" not in resposta.text
    assert set(resposta.context["consultas"][0]) == {
        "id", "paciente_id", "profissional_id", "horario", "status",
    }


def test_agenda_vazia(client):
    resposta = client.get("/agenda?dia=2026-10-03")
    assert resposta.status_code == 200
    assert "Nenhuma consulta agendada para este dia." in resposta.text


def test_agenda_sem_parametro_usa_dia_atual_da_clinica(client, monkeypatch):
    class RelogioFixo:
        @staticmethod
        def now(fuso):
            assert fuso == FUSO_CLINICA
            return datetime(2026, 10, 3, 23, 59, tzinfo=fuso)

    monkeypatch.setattr("app.routes.agenda.datetime", RelogioFixo)
    criar(client)
    resposta = client.get("/agenda")
    assert resposta.status_code == 200
    assert "Consultas de 03/10/2026" in resposta.text
    assert len(resposta.context["consultas"]) == 1


def test_agenda_rejeita_dia_invalido(client):
    assert client.get("/agenda?dia=2026-02-30").status_code == 422


def test_agenda_converte_instante_utc_antes_de_filtrar_dia(client):
    criar(client, "2026-10-04T01:00:00Z")  # 22h do dia anterior na clínica
    resposta = client.get("/agenda?dia=2026-10-03")
    assert len(resposta.context["consultas"]) == 1
    assert "22:00" in resposta.text
    assert not client.get("/agenda?dia=2026-10-04").context["consultas"]


@pytest.mark.parametrize("payload", [
    "<script>alert(1)</script>",
    '<img src=x onerror="alert(1)">',
])
def test_agenda_escapa_texto_malicioso_armazenado(client, payload):
    consulta_id = criar(client).json()["id"]
    resposta = client.patch(f"/consultas/{consulta_id}", json={"status": payload})
    assert resposta.status_code == 200
    armazenada = obter_consulta_por_id(consulta_id)
    assert armazenada is not None
    assert armazenada.status == payload
    pagina = client.get("/agenda?dia=2026-10-03")
    assert payload not in pagina.text
    html = InspecionarHTML()
    html.feed(pagina.text)
    assert payload in html.textos
    assert "script" not in html.tags
    assert "img" not in html.tags
