# Evidências do Exercício 5 — Arquitetura de segurança

## Artefatos e rubrica

| Artefato | Demonstração de R09 |
| --- | --- |
| [Relatório de arquitetura](../../docs/arquitetura-seguranca.md) | Partições, responsabilidades, estado atual/futuro, fluxos, fronteiras, vetores e decisões prévias à autenticação |
| [Fonte Mermaid](../../docs/particoes-seguranca.mmd) | Componentes atuais com pares de fluxo do DFD; controles/substituições planejados separados |
| [SVG exportado](particoes-seguranca.svg) e [screenshot real](particoes-seguranca.png) | Diagrama legível renderizado no Chromium, inspecionado visualmente |
| [Revisão documental](revisao_documental.md) | Correspondência com código/DFD/threat model e conferência dos três eixos |
| [Baseline e hashes](baseline.txt) | Commit analisado, hashes dos documentos/código/artefatos e verificações executadas |

Documentos relacionados: [CIA/DFD](../../docs/cia-dfd.md), [threat model](../../docs/threat-model.md), [decisões DEC-17](../../docs/decisoes.md) e [rastreabilidade](../../docs/rastreabilidade.md). Snapshot do modelo 1.0 e evidências dos incrementos anteriores permanecem históricos; não foram reescritos.

## Renderização realizada

Mermaid **10.9.3**, já disponível temporariamente fora das dependências da API, renderizou a fonte em um HTML local com `securityLevel: 'strict'`, `htmlLabels: false` e `startOnLoad: false`. Chromium headless produziu DOM e PNG; `data-rendered="true"` confirmou conclusão e o SVG foi extraído do DOM. O print foi inspecionado: atuais dentro de TB-01; memória marcada com TB-02 lógico; plano futuro separado com linhas pontilhadas.

Comando de captura executado (arquivos temporários removidos após exportação):

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex05-chromium --virtual-time-budget=10000 \
  --window-size=2600,1100 \
  --screenshot="$PWD/evidencias/ex05/particoes-seguranca.png" --dump-dom \
  "file://$PWD/.particoes-render-ex05.html"
```

`--no-sandbox` foi usado apenas para renderizar fonte local fictícia, não como configuração de navegação externa ou da aplicação. Para consultar novamente o resultado, abrir o SVG/PNG ou o bloco Mermaid do relatório; para atualizar o desenho, usar a fonte `.mmd` com um renderizador compatível e conferir as relações antes de exportar.

## Verificação e limites

Foram examinados quatro vetores por eixo (design, implementação e infraestrutura), os controles CTRL-01–11, fluxos F-01–10 e fronteiras atuais/lógicas/futuras. A análise de acesso permitido/proibido é design planejado, não execução de rotas já protegidas. A aplicação ainda não possui JWT, sessão HTML, M2M, SQLModel, hardening ou ambiente de produção demonstrado.

Testes JSON/XSS dos Ex. 1/2 são evidências históricas citadas no relatório. Nesta etapa não houve pytest, scan, carga, teste concorrente, autenticação ou query relacional. Não há scores CVSS, novas vulnerabilidades demonstradas ou autorização de deploy.
