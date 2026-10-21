# Revisão documental — Exercício 5

Baseline: `e2f239badbaa6905ef32cdfe9423e0fa33b61065`. Inspeção de código, documentos e evidências existentes, sem alteração funcional.

## Conferências

- P-01/P-02/P-03/D-01 correspondem a rotas, HTML, dados e memória.
- Auth/middleware/banco/M2M eram planejados; pastas não criavam isolamento.
- F-01–10 e fronteiras preservados; visão de partições agrupa ida/retorno.
- R09: quatro vetores por eixo, doze no total, com TM/CTRL/TEST.
- CTRL-01–11 localizados; JWT compartilhado, ownership com recurso/vínculo, JSON e HTML sob política.
- Decisões pendentes: matriz/vínculo, sessão HTML, JWT/MFA, regras de agenda e banco/TLS/recuperação.

## Registro

Fontes oficiais estão no relatório correspondente em `docs/`. Mermaid 10.9.3/Chromium produziu as exportações quando aplicável; baselines e hashes registram a versão examinada na época. Documentos de trabalho evoluíram depois desses registros.

Não houve nova execução de pytest, scanner, carga ou exploração nesta revisão. Evidências funcionais reutilizadas pertencem ao Ex. 2.
