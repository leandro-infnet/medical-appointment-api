# Evidências — Exercício 2

16 testes aprovados; response models com seis campos, Jinja2 com herança e auto-escape. R02–R04; justificativa em [DEC-13](../../docs/decisoes.md).

| Critério | Implementação | Evidência |
| --- | --- | --- |
| R02: controle preciso das respostas | `ConsultaResponse` nas quatro operações JSON; só seis campos autorizados | [respostas_http.json](respostas_http.json): armazenamento contém campos internos ausentes nas respostas; [pytest_output.txt](pytest_output.txt) |
| R03: justificar risco de exposição | [DEC-13](../../docs/decisoes.md): o contrato anterior declarava notas e auditoria; allowlist própria reduz vazamentos | Evidência histórica do Ex. 1 comparada com JSON atual e teste de preservação do armazenamento |
| R04: herança Jinja2 e proteção XSS | `agenda.html` estende `base.html`; auto-escape explícito e contexto mínimo | [agenda_xss.html](agenda_xss.html), [agenda_xss.png](agenda_xss.png), [payloads.json](payloads.json), testes com script e imagem/handler |

`pytest_output.txt` registra a suíte; `ambiente_versao.txt` registra versões; `agenda_vazia.html` mostra dia sem consultas. O PNG foi capturado do HTML local recebido da rota, com script exibido como texto.

## Reprodução histórica

Usar baseline do Ex. 2, anterior à autenticação; comandos originais:

```bash
.venv/bin/python -m pytest tests/ -v
.venv/bin/python evidencias/ex02/reproduzir.py
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex02-chromium \
  --screenshot="$PWD/evidencias/ex02/agenda_xss.png" --window-size=1100,800 \
  "file://$PWD/evidencias/ex02/agenda_xss.html"
```

Preservar as saídas anteriores. Chromium é ferramenta de captura, não dependência da API; no-sandbox foi limitado ao HTML local fictício. O screenshot não é login/navegação conectada.
