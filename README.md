# API de Agendamento de Consultas Médicas

API REST desenvolvida com FastAPI para agendamento de consultas médicas em uma rede de clínicas. O desenvolvimento é incremental: esta primeira etapa entrega o CRUD modular de consultas; os controles de exposição, autenticação, autorização e persistência segura estão previstos nos exercícios seguintes.

## Requisitos

- Python 3.11+ (desenvolvido e testado com Python 3.14)
- Ambiente virtual isolado (`.venv`)

## Instalação

1. Clone o repositório e navegue até a pasta do projeto:
```bash
cd /caminho/do/projeto
```

2. Crie e ative o ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -e ".[dev]"
```

O manifesto declara versões mínimas. As versões usadas na demonstração do Exercício 1 estão em `evidencias/ex01/ambiente_versao.txt`; ainda não há lockfile.

## Execução do Servidor

Para iniciar a aplicação com recarregamento automático (modo de desenvolvimento):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

A documentação interativa OpenAPI (Swagger UI) estará disponível em:
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Execução dos Testes Automatizados

Para rodar a suíte de testes com pytest:

```bash
.venv/bin/python -m pytest tests/ -v
```

## Estrutura de Módulos

A aplicação segue a organização modular de responsabilidades separadas:
- `app/main.py`: Ponto de entrada e composição da aplicação FastAPI.
- `app/routes/`: Roteadores HTTP (`APIRouter`) tratando requisições, status e parâmetros.
- `app/models/`: Schemas Pydantic para validação de entrada e saída.
- `app/database/`: Camada de gerenciamento de dados e persistência.
- `docs/`: Documentação técnica de arquitetura, requisitos e decisões.
- `evidencias/`: Evidências de execução de cada exercício do Assessment.
- `tests/`: Suíte de testes automatizados com pytest.
