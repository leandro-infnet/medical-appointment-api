# Evidências — Exercício 11

Persistência SQLModel em arquivo SQLite, configuração BaseSettings/`.env`, queries parametrizadas e sessão por requisição. Decisões e limites em [persistencia.md](../../docs/persistencia.md); schema em `app/models/tabelas.py` e DFD atualizado em `docs/dfd-atual.mmd` (fonte, sem nova exportação gráfica).

| Artefato | O que comprova |
| --- | --- |
| `pytest_output.txt` | Saída real de `.venv/bin/python -m pytest tests/ -q --tb=short`: 181 testes passaram, dois avisos de dependências |
| `reproduzir.py` | Cria banco/cadastro temporários, executa dois processos independentes e remove dados no término |
| `execucao.txt`, `avisos.txt` | Saídas reais do script, sem senhas/tokens/caminhos de configuração sensível |
| `resultados.json` | Treze observações HTTP; INSERT com placeholders/parâmetros; leitura após reinício, ownership, agenda, M2M, 409/rollback e exclusão |
| `ambiente.json` | Versões reais de Python, SQLite, SQLModel, SQLAlchemy, Pydantic, FastAPI e pytest |
| `../../.env.example` | Configuração demonstrativa sem segredo ou credencial real; SQLite não usa usuário/senha |

Reproduzir no incremento atual, após instalar as dependências:

```bash
.venv/bin/python -m pytest tests/ -q --tb=short
.venv/bin/python evidencias/ex11/reproduzir.py
```

O script escreve os JSONs; para preservar stdout/stderr, redirecionar para `execucao.txt`/`avisos.txt`. Não usa `.local` real nem importa pacientes reais. Os dezoito testes novos exercitam o SQLite escolhido, incluindo duas disputas concorrentes, constraints/FK, fechamento de sessão, rollback e 503 com timeout controlado. Os demais casos são regressões dos exercícios anteriores.

A prova de reinício usa processos independentes com TestClient e o mesmo arquivo temporário. Não comprova Uvicorn/TLS, backup/restauração, carga, ZAP ou deploy. As evidências de memória nos exercícios anteriores não foram alteradas. Scripts antigos devem ser executados nos respectivos baselines; a reprodução Ex. 11 usa a aplicação atual.
