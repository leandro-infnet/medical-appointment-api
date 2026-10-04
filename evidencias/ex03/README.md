# Evidências do Exercício 3 — CIA e DFD

## Artefatos entregues

| Artefato | Finalidade / rubrica |
| --- | --- |
| [Relatório CIA e DFD](../../docs/cia-dfd.md) | CIA-01–08, AT-01–06, controles existentes, lacunas e mapeamento OWASP/NIST SSDF/MITRE; R05/R06 |
| [Fonte Mermaid](../../docs/dfd-atual.mmd) | Estado real: consumidores JSON/HTML, três processos lógicos e memória temporária; dez fluxos; R06 |
| [DFD exportado em SVG](dfd-atual.svg) | Diagrama vetorial legível para ampliar e incluir no relatório |
| [Print real do DFD](dfd-atual.png) | Renderização do Mermaid no Chromium headless, inspecionada visualmente |
| [Revisão documental](revisao_documental.md) | Verificações dos percursos, dados, controles, fronteiras e limites da etapa |
| [Baseline e hashes](baseline.txt) | Commit/branch analisados e hashes do relatório, fonte e código inspecionado |

O relatório é o documento técnico desta etapa e deve acompanhar estes artefatos no ZIP. Não é necessário duplicá-lo nesta pasta. Evidências de execução dos controles reutilizadas: [JSON/HTML Ex. 2](../ex02/README.md), [pytest Ex. 2](../ex02/pytest_output.txt) e [fundação Ex. 1](../ex01/README.md).

## Renderização efetivamente executada

Mermaid **10.9.3** foi obtido como ferramenta temporária de exportação, sem alteração das dependências Python. Um HTML temporário carregou a fonte `.mmd` com `mermaid.render`, `securityLevel: 'strict'`, `htmlLabels: false` e `startOnLoad: false`. O Chromium executou a renderização com orçamento virtual de 10 segundos e produziu DOM e screenshot. O indicador `data-rendered="true"` foi conferido; o SVG foi extraído do DOM renderizado e salvo.

Comando final de captura utilizado, na raiz (arquivos temporários removidos após exportação):

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex03-chromium --virtual-time-budget=10000 \
  --window-size=2200,650 \
  --screenshot="$PWD/evidencias/ex03/dfd-atual.png" --dump-dom \
  "file://$PWD/.dfd-render-ex03.html"
```

`--no-sandbox` foi usado para renderizar exclusivamente fonte local fictícia, sem navegar entradas externas; não é recomendação de navegação de produção. Houve aviso DBus, sem impedir a exportação. Para visualizar novamente, abrir `dfd-atual.svg` ou o Mermaid do relatório em um visualizador compatível. Para atualizar a exportação, usar a fonte `.mmd` com Mermaid 10.9.3; conservar IDs e conferir novamente fluxos e fronteiras. Ferramentas de renderização não fazem parte da API.

## Critérios atendidos

- **R05:** análise de C/I/A com consequências e limites, mais controle → código → teste/evidência em OWASP, NIST SSDF e MITRE. As fontes oficiais estão ligadas aos itens no relatório.
- **R06:** DFD básico com dados de pacientes, consumidores, processos, depósito, fluxos direcionados e trust boundary externa. O limite lógico dos dados internos é explicitamente distinto de isolamento de processo; parceiro e banco são futuros.

O Ex. 3 altera documentação e artefatos de evidência. Não altera endpoints, modelos, templates nem testes da aplicação. Não houve nova execução de pytest, Uvicorn, ZAP, teste de carga ou teste concorrente. O baseline de testes do Ex. 2 permanece histórico: 16 testes passaram. A ausência de autorização e a perda dos dados após reinício continuam registradas, sem alegação de liberação para produção.
