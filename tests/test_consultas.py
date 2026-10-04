"""Testes automatizados do recurso RESTful de Consultas (Exercício 1)."""

from fastapi import status


def test_criar_consulta_sucesso(client):
    """
    Testa o caminho de sucesso na criação de uma consulta via POST /consultas.
    Requisito explícito do Exercício.
    """
    payload = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-15T14:30:00",
        "motivo": "Consulta de rotina cardiológica",
        "observacoes_internas": "Paciente alérgico a dipirona."
    }

    resposta = client.post("/consultas", json=payload)

    assert resposta.status_code == status.HTTP_201_CREATED
    dados = resposta.json()
    assert dados["id"] == 1
    assert dados["paciente_id"] == payload["paciente_id"]
    assert dados["profissional_id"] == payload["profissional_id"]
    assert dados["motivo"] == payload["motivo"]
    assert dados["status"] == "agendada"
    assert "data_hora" in dados


def test_listar_consultas(client):
    """Testa a listagem de consultas via GET /consultas."""
    c1 = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-15T10:00:00",
        "motivo": "Avaliação inicial"
    }
    c2 = {
        "paciente_id": 2,
        "profissional_id": 1,
        "data_hora": "2026-10-15T11:00:00",
        "motivo": "Retorno ortopédico"
    }
    client.post("/consultas", json=c1)
    client.post("/consultas", json=c2)

    resposta = client.get("/consultas")
    assert resposta.status_code == status.HTTP_200_OK
    consultas = resposta.json()
    assert len(consultas) == 2


def test_obter_consulta_por_id_sucesso(client):
    """Testa a recuperação de uma consulta existente por ID via GET /consultas/{id}."""
    payload = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-16T09:00:00",
        "motivo": "Exame preventivo"
    }
    criacao = client.post("/consultas", json=payload)
    consulta_id = criacao.json()["id"]

    resposta = client.get(f"/consultas/{consulta_id}")
    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert dados["id"] == consulta_id
    assert dados["motivo"] == payload["motivo"]


def test_obter_consulta_inexistente_retorna_404(client):
    """Testa o comportamento de consulta não encontrada via GET /consultas/{id}."""
    resposta = client.get("/consultas/9999")
    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert "não encontrada" in resposta.json()["detail"]


def test_atualizar_consulta_sucesso(client):
    """Testa a atualização parcial de consulta via PATCH /consultas/{id}."""
    payload = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-18T15:00:00",
        "motivo": "Fisioterapia pós-operatória"
    }
    criacao = client.post("/consultas", json=payload)
    consulta_id = criacao.json()["id"]

    atualizacao = {
        "status": "realizada",
        "motivo": "Fisioterapia concluída com sucesso"
    }
    resposta = client.patch(f"/consultas/{consulta_id}", json=atualizacao)
    assert resposta.status_code == status.HTTP_200_OK
    dados = resposta.json()
    assert dados["status"] == "realizada"
    assert dados["motivo"] == "Fisioterapia concluída com sucesso"


def test_remover_consulta_sucesso(client):
    """Testa a remoção de consulta via DELETE /consultas/{id}."""
    payload = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-20T08:30:00",
        "motivo": "Consulta para cancelamento"
    }
    criacao = client.post("/consultas", json=payload)
    consulta_id = criacao.json()["id"]

    resposta_delete = client.delete(f"/consultas/{consulta_id}")
    assert resposta_delete.status_code == status.HTTP_204_NO_CONTENT

    # Confirma que foi removida
    resposta_busca = client.get(f"/consultas/{consulta_id}")
    assert resposta_busca.status_code == status.HTTP_404_NOT_FOUND


def test_estado_reiniciado_entre_testes(client):
    """A fixture deve limpar registros e reiniciar os IDs entre testes."""
    assert client.get("/consultas").json() == []
    resposta = client.post("/consultas", json={
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-21T09:00:00",
        "motivo": "Consulta de rotina",
    })
    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.json()["id"] == 1


def test_patch_nulo_rejeitado_sem_corromper_consulta(client):
    """Campos obrigatórios não podem virar nulos por atualização parcial."""
    criacao = client.post("/consultas", json={
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-21T09:00:00",
        "motivo": "Consulta de rotina",
    })
    assert criacao.status_code == status.HTTP_201_CREATED
    consulta_id = criacao.json()["id"]

    for campo in ("data_hora", "status", "motivo"):
        resposta = client.patch(f"/consultas/{consulta_id}", json={campo: None})
        assert resposta.status_code == 422
        assert client.get(f"/consultas/{consulta_id}").json() == criacao.json()
