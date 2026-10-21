# Evidências — Exercício 5

Análise documental: partições e doze vetores de design/implementação/infraestrutura; R09. [Relatório](../../docs/arquitetura-seguranca.md).

| Artefato | Demonstração de R09 |
| --- | --- |
| [Relatório de arquitetura](../../docs/arquitetura-seguranca.md) | Partições, responsabilidades, estado atual/futuro, fluxos, fronteiras, vetores e decisões prévias à autenticação |
| [Fonte Mermaid](../../docs/particoes-seguranca.mmd) | Componentes atuais com pares de fluxo do DFD; controles/substituições planejados separados |
| [SVG exportado](particoes-seguranca.svg) e [screenshot real](particoes-seguranca.png) | Diagrama legível renderizado no Chromium, inspecionado visualmente |
| [Revisão documental](revisao_documental.md) | Correspondência com código/DFD/threat model e conferência dos três eixos |
| [Baseline e hashes](baseline.txt) | Commit analisado, hashes dos documentos/código/artefatos e verificações executadas |

## Exportação histórica

Mermaid 10.9.3 em HTML local: securityLevel strict, htmlLabels false, startOnLoad false. Chromium renderizou com orçamento de 10 s; SVG extraído do DOM e PNG inspecionado. Comando usado:

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex05-chromium --virtual-time-budget=10000 \
  --window-size=2600,1100 \
  --screenshot="$PWD/evidencias/ex05/particoes-seguranca.png" --dump-dom \
  "file://$PWD/.particoes-render-ex05.html"
```

Arquivos temporários da exportação foram removidos. no-sandbox foi usado apenas no conteúdo fictício local; não configura a API. Para nova exportação, renderizar a fonte Mermaid e conferir IDs/fluxos. Os arquivos desta pasta preservam a arquitetura daquele baseline, não o DFD final.

A etapa não executou pytest/scanner/ataques. Testes citados dos Ex. 1/2 são históricos. Baseline e revisão registram as verificações documentais.
