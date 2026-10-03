# Evidências do Exercício 2

## Resultado e rubrica

| Critério | Implementação | Evidência |
| --- | --- | --- |
| R02: controle preciso das respostas | `ConsultaResponse` nas quatro operações JSON; só seis campos autorizados | [respostas_http.json](respostas_http.json): armazenamento contém campos internos ausentes nas respostas; [pytest_output.txt](pytest_output.txt) |
| R03: justificar risco de exposição | [DEC-13](../../docs/decisoes.md): o contrato anterior declarava notas e auditoria; allowlist própria reduz vazamentos | Evidência histórica do Ex. 1 comparada com JSON atual e teste de preservação do armazenamento |
| R04: herança Jinja2 e proteção XSS | `agenda.html` estende `base.html`; auto-escape explícito e contexto mínimo | [agenda_xss.html](agenda_xss.html), [agenda_xss.png](agenda_xss.png), [payloads.json](payloads.json), testes com script e imagem/handler |

## Artefatos efetivamente gerados

- [pytest_output.txt](pytest_output.txt): `.venv/bin/python -m pytest tests/ -v`; **16 passed**, dois avisos de depreciação de Starlette/httpx e alias AnyIO. A primeira execução detectou apenas uma diferença de representação de entidades HTML no teste; a verificação final usa parsing HTML para comprovar texto e ausência das tags executáveis.
- [ambiente_versao.txt](ambiente_versao.txt): versões instaladas desta etapa; Python 3.14.4. `pip install -e '.[dev]'` concluiu, incluindo tzdata.
- [respostas_http.json](respostas_http.json): respostas HTTP reais em processo via TestClient (POST, GET individual/listagem, PATCH e agenda), campos armazenados e campos mínimos no contexto HTML.
- [payloads.json](payloads.json): criação fictícia e ataque didático no status; sem dados ou credenciais reais.
- [agenda_xss.html](agenda_xss.html): corpo recebido da rota; `<script>alert(1)</script>` persistido em memória é recebido como `&lt;script&gt;alert(1)&lt;/script&gt;`.
- [agenda_vazia.html](agenda_vazia.html): estado vazio de outro dia.
- [agenda_xss.png](agenda_xss.png): screenshot real do HTML acima aberto no Chromium headless, com o script apresentado como texto. O print foi inspecionado; não é uma imagem simulada.

## Como reproduzir

Na raiz, com dependências instaladas:

```bash
.venv/bin/python -m pytest tests/ -v
.venv/bin/python evidencias/ex02/reproduzir.py
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex02-chromium \
  --screenshot="$PWD/evidencias/ex02/agenda_xss.png" --window-size=1100,800 \
  "file://$PWD/evidencias/ex02/agenda_xss.html"
```

`--no-sandbox` foi usado somente para a captura local de um arquivo fictício; não é configuração recomendada para navegar conteúdo externo. Chromium gerou o PNG apesar de avisos do Snap/DBus. Adapte o executável ao sistema; Chromium é auxiliar para evidência, não dependência da API.

O gerador utiliza processo e memória próprios, limpa antes/depois e não afeta um servidor Uvicorn em execução. A captura usa o HTML salvo; o formulário no screenshot não representa uma sessão conectada ao servidor. Para demonstração interativa, iniciar Uvicorn conforme README, criar uma consulta e abrir `/agenda?dia=2026-10-03`.

## Limites e continuidade

A memória representa persistência apenas durante este processo; SQLModel será introduzido no Ex. 11. O status ainda aceita texto livre, comportamento anterior utilizado no experimento; catálogo de estados será definido antes da validação estrita. Autenticação e autorização estão pendentes para o Ex. 6: minimização/escape não impedem acesso anônimo nem BOLA. Fuso provisório: `America/Sao_Paulo` (DEC-14).

Rastreabilidade: [docs/rastreabilidade.md](../../docs/rastreabilidade.md). Reutilizar testes e payloads na modelagem de ameaças, correção XSS e auditoria final, preservando estas evidências históricas.
