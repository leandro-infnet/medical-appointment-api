# Evidências — Exercício 4

Baseline `fe31673e1ed4e0238277abe0b111d66be1363c9e`. R07/R08: 12 misuse cases, seis categorias STRIDE em três componentes (18 avaliações) e 16 ameaças iniciais.

| Arquivo | Conteúdo |
| --- | --- |
| [Modelo inicial](threat-model-v1.md) | Análise do baseline; IDs e conclusões preservados |
| [Revisão](revisao_documental.md) | Conferências de código, DFD, controles e limites |
| [Baseline](baseline.txt) | Commit, verificações e hashes da versão original |
| [Modelo atual](../../docs/threat-model.md) | Fechamento dos controles/testes e riscos residuais |
| [DFD histórico](../ex03/dfd-atual.svg) | Fluxos/componentes usados na análise inicial |

CTRL-03/04 já tinham prova histórica: [JSON Ex. 2](../ex02/respostas_http.json), [HTML](../ex02/agenda_xss.html), [PNG](../ex02/agenda_xss.png) e [pytest](../ex02/pytest_output.txt). Demais cenários eram planejados; não houve pytest, scanner ou exploração no Ex. 4.

Documentos receberam revisão de redação; hashes em baseline.txt correspondem à versão inicial, não à redação atual. Fontes de código, logs e exportações permanecem preservados. [Rastreabilidade](../../docs/rastreabilidade.md).
