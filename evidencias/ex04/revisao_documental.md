# Revisão documental — Exercício 4

Baseline: `fe31673e1ed4e0238277abe0b111d66be1363c9e`. Inspeção de código, documentos e evidências existentes, sem alteração funcional.

## Conferências

- R07: 12 misuse cases com ator, precondição, tentativa e vínculo TM/CTRL/TEST.
- R08: seis categorias STRIDE em P-01/P-02/P-03, 18 avaliações.
- AT-01–06/F-01–10/TB-01–04 mantidos; TM-001–016 e CTRL-01–11 rastreáveis.
- Cenários futuros JWT/M2M/SQL separados; TEST-19–22 propostos, sem execução.
- Política por recurso inclui lista/HTML/mutação; PATCH não troca profissional; extras ignorados não eram promoção comprovada.
- Lock não garante sobreposição/durabilidade; risco residual mantém cobertura parcial explícita.

## Registro

Fontes oficiais estão no relatório correspondente em `docs/`. Mermaid 10.9.3/Chromium produziu as exportações quando aplicável; baselines e hashes registram a versão examinada na época. Documentos de trabalho evoluíram depois desses registros.

Não houve nova execução de pytest, scanner, carga ou exploração nesta revisão. Evidências funcionais reutilizadas pertencem ao Ex. 2. O histórico do Ex. 4 está em `threat-model-v1.md`; estados atuais em `docs/threat-model.md`.
