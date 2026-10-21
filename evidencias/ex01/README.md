# Evidências — Exercício 1

Fundação com APIRouter e módulos routes/models/database. Python 3.14.4, instalação editável e ambiente virtual isolado.

| Arquivo | Resultado |
| --- | --- |
| `ambiente_versao.txt`, `instalacao_editavel.txt` | Versões e instalação `pip install -e '.[dev]'` |
| `uvicorn_server.log`, `uvicorn_respostas_rotas.txt` | Uvicorn 127.0.0.1:8000 e respostas via curl de POST/GET/PATCH/DELETE |
| `pytest_output.txt`, `pytest_revisao.txt` | Seis testes iniciais; oito após revisão, incluindo null no PATCH e IDs isolados |

Rotas: criação 201, leitura/lista/atualização 200, remoção física 204, recurso ausente 404. Teste de sucesso em `tests/test_consultas.py`.

Baseline em memória, sem autenticação/vínculo; notas ainda apareciam no JSON. As etapas seguintes restringem saída, acesso e persistência. Estes registros são históricos. [Estado final](../../docs/relatorio-capstone.md).
