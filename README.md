# API de Agendamento de Consultas Médicas

API REST desenvolvida com FastAPI para agendamento de consultas médicas em uma rede de clínicas. Os Exercícios 1 e 2 entregam o CRUD modular, respostas JSON com campos controlados e agenda diária HTML com herança Jinja2 e escape de saída. Autenticação, autorização e persistência relacional serão introduzidas nos exercícios seguintes; execute esta etapa somente localmente com dados fictícios.

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

As versões do Exercício 2 constam em `evidencias/ex02/ambiente_versao.txt`. `tzdata` fornece a base de fusos IANA quando ela não existe no sistema operacional.

## Execução do Servidor

Para iniciar a aplicação com recarregamento automático (modo de desenvolvimento):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

A documentação interativa OpenAPI (Swagger UI) estará disponível em:
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Consultas e agenda diária

As respostas de criação, listagem, leitura e atualização contêm somente `id`, `paciente_id`, `profissional_id`, `data_hora`, `motivo` e `status`. `observacoes_internas`, `criado_em` e `atualizado_em` permanecem no armazenamento, mas não saem no JSON.

Abra [http://127.0.0.1:8000/agenda](http://127.0.0.1:8000/agenda) para o dia atual da clínica, ou `/agenda?dia=2026-10-03` para uma data explícita. A página apresenta horário, IDs de consulta/paciente/profissional e status; não recebe motivo clínico nem notas internas. Data inválida resulta em HTTP 422; dia vazio tem mensagem própria.

**Recomendação de engenharia adotada provisoriamente:** `America/Sao_Paulo` como fuso da clínica. Horários sem offset são interpretados nesse fuso; horários com offset são convertidos antes de filtrar o dia. Esta convenção não foi imposta pelo Assessment e deve ser confirmada antes da persistência/disponibilidade. A escolha é explicada em [docs/decisoes.md](docs/decisoes.md).

A agenda ainda não restringe acesso à recepção: autenticação e autorização pertencem ao Exercício 6. Escape HTML evita interpretação das entradas como marcação; não substitui controle de acesso.

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
- `app/templates/`: Layout HTML compartilhado (`base.html`) e agenda que o estende, com auto-escape explícito.
- `docs/`: Documentação técnica de arquitetura, requisitos e decisões.
- `evidencias/`: Evidências de execução de cada exercício do Assessment.
- `tests/`: Suíte de testes automatizados com pytest.

## Evidências do Exercício 2

[evidencias/ex02/README.md](evidencias/ex02/README.md) relaciona requisitos, testes, respostas HTTP, HTML e screenshot real. Para regenerar os artefatos JSON/HTML em memória isolada:

```bash
.venv/bin/python evidencias/ex02/reproduzir.py
```

O script não se conecta a banco ou servidor existente. Os testes e as evidências do Exercício 1 foram preservados como registro histórico.
