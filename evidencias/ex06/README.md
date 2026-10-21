# Evidências — Exercício 6

Baseline: `fb75b016ed9e535fbb4bf1715af2b8a91f697bdf`. R10/R11: bearer, bcrypt, JWT, ownership e MFA simulado. Matriz e transporte em [contrato humano](../../docs/autenticacao-autorizacao.md).

| Arquivo | Origem e alcance |
| --- | --- |
| `pytest_output.txt` | Saída completa de `.venv/bin/python -m pytest tests/ -v`: **60 passed**, dois avisos de dependências, sem testes pulados |
| `respostas_http.json` | 21 cenários HTTP efetivamente executados por `reproduzir.py`; senha/token/hash/desafio/fator omitidos |
| `ambiente.json` | Versões efetivamente instaladas no processo de reprodução |
| `agenda_autenticada.html` | HTML obtido por GET com cookie da recepção; espaços finais normalizados; contexto mínimo, dados fictícios |
| `agenda_autenticada.png` | Renderização pelo Chromium do HTML salvo; não é teste de login/navegação no navegador conectado à API |
| `dfd-atual.svg`, `dfd-atual.png` | Renderização local Mermaid 10.9.3 da fonte atual, com identidade/políticas/cadastro/desafios; fonte em `docs/dfd-atual.mmd` |

60 testes: 16 regressões anteriores e 44 casos novos. HTTP: 21 cenários, incluindo anônimo 401, profissional/vínculo permitido, acesso cruzado 404, não admin 403, MFA 202→401/200 e replay negado. Cookie da recepção abre agenda, não JSON.

## Reprodução histórica

No baseline Ex. 6; preservar artefatos antes de executar os comandos originais:

```bash
.venv/bin/python -m pytest tests/ -v > evidencias/ex06/pytest_output.txt
.venv/bin/python evidencias/ex06/reproduzir.py
```

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex06-agenda-chromium \
  --screenshot="$PWD/evidencias/ex06/agenda_autenticada.png" --window-size=1100,800 \
  "file://$PWD/evidencias/ex06/agenda_autenticada.html"
```

Cadastro/segredos aleatórios e memória isolados. DFD: Mermaid 10.9.3/Chromium headless, arquivo local. O HTML/PNG não comprova login conectado em browser, TLS ou CSRF. Código MFA é estático e estado por worker; logout não revoga cópia de JWT.

Revisão posterior de OpenAPI/legibilidade: 52 testes de autorização/consultas e os 21 cenários HTTP passaram; templates não foram repetidos nessa revisão. Pylance/SonarLint não foram executados via CLI. Registros brutos de cada execução foram mantidos.
