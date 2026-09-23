# Evidências do Exercício 1 — Fundação da API de Agendamento

## 1. Ambiente Virtual e Configuração Isolada
- **Python:** 3.14.4 (conforme [ambiente_versao.txt](ambiente_versao.txt))
- **Gerenciador de Dependências:** `pyproject.toml` declarando `fastapi`, `uvicorn`, `pydantic`, `jinja2`, `pytest` e `httpx`.
- **Isolamento:** `.venv` ativado e testado localmente.
- **Instalação editável verificada na revisão:** `pip install -e '.[dev]'` concluiu no ambiente virtual; registro em [instalacao_editavel.txt](instalacao_editavel.txt).

## 2. Modularização Arquitetural
A aplicação foi estruturada estritamente nos módulos exigidos pelo Assessment:
- `app/routes/`: Contém [consultas.py](../../app/routes/consultas.py) implementando o recurso RESTful via `APIRouter(prefix="/consultas")`.
- `app/models/`: Contém [consultas.py](../../app/models/consultas.py) com schemas Pydantic de entrada e domínio (`ConsultaBase`, `ConsultaCreate`, `ConsultaUpdate`, `Consulta`).
- `app/database/`: Contém [memoria.py](../../app/database/memoria.py) e [consultas.py](../../app/database/consultas.py) gerenciando o armazenamento em memória e isolamento thread-safe.
- `app/main.py`: Ponto de entrada com a composição da aplicação FastAPI sem regras de negócio ou banco acoplados.

## 3. Recurso RESTful Completo de Consultas
Endpoints implementados e verificados:
- `POST /consultas`: Criação de consulta (Status HTTP 201 Created).
- `GET /consultas`: Listagem geral com filtros opcionais (Status HTTP 200 OK).
- `GET /consultas/{id}`: Obtenção por ID com tratamento de erro (Status HTTP 200 OK ou 404 Not Found).
- `PATCH /consultas/{id}`: Atualização parcial de campos permitidos (Status HTTP 200 OK ou 404 Not Found).
- `DELETE /consultas/{id}`: Remoção/cancelamento de consulta (Status HTTP 204 No Content ou 404 Not Found).

## 4. Execução do Servidor Uvicorn e Resposta Real das Rotas
O servidor Uvicorn foi executado em `127.0.0.1:8000` e as requisições HTTP foram enviadas via `curl`.
- Log do servidor Uvicorn registrado em [uvicorn_server.log](uvicorn_server.log).
- Respostas completas das rotas (cabeçalhos HTTP e JSON retornado) registradas em [uvicorn_respostas_rotas.txt](uvicorn_respostas_rotas.txt).

## 5. Testes Automatizados com Pytest
- Suíte configurada em [tests/conftest.py](../../tests/conftest.py) com fixture de limpeza de banco e `TestClient(app)`.
- Testes implementados em [tests/test_consultas.py](../../tests/test_consultas.py), cobrindo o caminho de sucesso de criação de consulta (`test_criar_consulta_sucesso`), além de listagem, busca por ID, 404, atualização e remoção.
- Execução inicial de seis testes registrada em [pytest_output.txt](pytest_output.txt). Após a revisão, oito testes passaram; resultado em [pytest_revisao.txt](pytest_revisao.txt), incluindo isolamento de IDs e rejeição de `null` no `PATCH`.

## 6. Limitações Conhecidas desta Etapa
- **Autenticação e Autorização:** Ainda não implementadas (previstas para o Exercício 6). Qualquer cliente que acesse o endpoint pode manipular consultas.
- **Exposição de Campos Internos:** O campo `observacoes_internas` ainda é retornado no JSON da consulta, risco que será mitigado no Exercício 2 via `response_model` estrito.
- **Persistência:** Dados em memória (a migração para SQLModel relacional está planejada para o Exercício 11).
- **Integridade referencial:** Os seeds fictícios ilustram IDs de pacientes/profissionais, mas a criação ainda não verifica se esses IDs existem ou se o paciente pertence ao profissional. A decisão e o controle ficam pendentes para os exercícios de autorização e persistência.
- **Regras de agenda:** Fuso, duração, conflitos e estados permitidos ainda precisam ser definidos antes da agenda diária e da disponibilidade externa.
