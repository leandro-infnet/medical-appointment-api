# Evidências do Exercício 4 — STRIDE e threat model

## Entrega e rubrica

| Artefato | Conteúdo / critério |
| --- | --- |
| [Threat model vivo](../../docs/threat-model.md) | Ativos, superfícies, 12 misuse cases, STRIDE em três componentes, ameaças, controles e testes; R07/R08 |
| [Snapshot inicial 1.0](threat-model-v1.md) | Estado inicial preservado para comparar com Ex. 12/13; links relativos adaptados à pasta de evidências |
| [Revisão documental](revisao_documental.md) | Correspondência com aplicação/DFD, cobertura e limites de prova |
| [Baseline e hashes](baseline.txt) | Revisão analisada e integridade dos documentos/código inspecionado |
| [DFD fonte](../../docs/dfd-atual.mmd), [SVG](../ex03/dfd-atual.svg) e [PNG](../ex03/dfd-atual.png) | Diagrama relacionado; o Ex. 4 não introduziu novos componentes/fluxos executáveis |

Rastreabilidade em [docs/rastreabilidade.md](../../docs/rastreabilidade.md); decisão DEC-16 em [docs/decisoes.md](../../docs/decisoes.md). As seis categorias STRIDE foram examinadas em P-01/P-02/P-03, com 18 avaliações. TM-001–012 descrevem estado atual, regressões, hipóteses ou condições; TM-013–016 são futuros.

## Evidências existentes reutilizadas

- **TM-004 / CTRL-03 / TEST-02:** [respostas HTTP Ex. 2](../ex02/respostas_http.json) e [pytest Ex. 2](../ex02/pytest_output.txt) comprovam o conjunto de campos do JSON e a preservação interna dos dados.
- **TM-005 / CTRL-04 / TEST-03:** [payloads](../ex02/payloads.json), [HTML escapado](../ex02/agenda_xss.html), [screenshot](../ex02/agenda_xss.png) e testes comprovam os contextos HTML exercitados.
- **TM-006 / CTRL-05 parcial:** teste histórico de PATCH nulo e data inválida; não comprova validação estrita de todos os campos ou vínculo paciente/profissional.

Essas provas são históricas do Exercício 2, não execuções realizadas no Ex. 4. O DFD/exportações do Ex. 3 são preservados, sem mudar seu baseline ou seus hashes anteriores.

## Verificações desta etapa

Inspeção do enunciado/rubrica, código, CIA/DFD e testes existentes; revisão de cada categoria em três componentes, referências cruzadas e separação entre controle atual/futuro. Snapshot e hashes são artefatos documentais. Não foram executados pytest, scans, ataques, carga, concorrência, JWT, M2M ou queries SQL nesta etapa. Não há scores CVSS ou security gate implementados.

Para reproduzir a revisão, conferir cada linha MU → TM → P/F/TB → CTRL → TEST no relatório, comparar a localização do controle com o código e a prova histórica com a evidência citada. O catálogo de testes indica preparação/caso permitido/negação esperada; cenários propostos só terão resultado quando executados nos incrementos correspondentes.

## Manutenção da versão inicial

O arquivo `threat-model-v1.md` é snapshot histórico, não o documento a atualizar em cada implementação. As mudanças posteriores devem ocorrer em `docs/threat-model.md`, conservando IDs e anotando controle, teste/evidência efetiva e risco residual. Não marcar ameaça como encerrada apenas por estar documentada ou ter controle parcial.
