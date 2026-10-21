# Evidências — Exercício 3

Análise documental: CIA-01–08, OWASP/SSDF/CWE e DFD F-01–10/TB-01–04; R05/R06. [Relatório](../../docs/cia-dfd.md).

| Artefato | Finalidade / rubrica |
| --- | --- |
| [Relatório CIA e DFD](../../docs/cia-dfd.md) | CIA-01–08, AT-01–06, controles existentes, lacunas e mapeamento OWASP/NIST SSDF/MITRE; R05/R06 |
| [Fonte Mermaid](../../docs/dfd-atual.mmd) | Estado real: consumidores JSON/HTML, três processos lógicos e memória temporária; dez fluxos; R06 |
| [DFD exportado em SVG](dfd-atual.svg) | Diagrama vetorial legível para ampliar e incluir no relatório |
| [Print real do DFD](dfd-atual.png) | Renderização do Mermaid no Chromium headless, inspecionada visualmente |
| [Revisão documental](revisao_documental.md) | Verificações dos percursos, dados, controles, fronteiras e limites da etapa |
| [Baseline e hashes](baseline.txt) | Commit/branch analisados e hashes do relatório, fonte e código inspecionado |

## Exportação histórica

Mermaid 10.9.3 em HTML local: securityLevel strict, htmlLabels false, startOnLoad false. Chromium renderizou com orçamento de 10 s; SVG extraído do DOM e PNG inspecionado. Comando usado:

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex03-chromium --virtual-time-budget=10000 \
  --window-size=2200,650 \
  --screenshot="$PWD/evidencias/ex03/dfd-atual.png" --dump-dom \
  "file://$PWD/.dfd-render-ex03.html"
```

Arquivos temporários da exportação foram removidos. no-sandbox foi usado apenas no conteúdo fictício local; não configura a API. Para nova exportação, renderizar a fonte Mermaid e conferir IDs/fluxos. Os arquivos desta pasta preservam a arquitetura daquele baseline, não o DFD final.

A etapa não executou pytest/scanner/ataques. Testes citados dos Ex. 1/2 são históricos. Baseline e revisão registram as verificações documentais.
