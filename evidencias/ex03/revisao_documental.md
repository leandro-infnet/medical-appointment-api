# Revisão documental — Exercício 3

Baseline: `46db788b99a19b4cf145555e8e9ff679a88e29fe`. Inspeção de código, documentos e evidências existentes, sem alteração funcional.

## Conferências

- CIA-01–08 relacionam ativos, impacto e controle.
- P-01 JSON/P-02 HTML/P-03 dados e D-01 memória correspondem ao código; F-01–10 têm origem/destino.
- TB-01 é exterior/processo; TB-02 é divulgação lógica; TB-03/04 eram futuras.
- OWASP API3/A03, SSDF PW.5.1/PW.8.2/PW.1.2 e CWE-79/200/20 estão associados a código/evidência.
- JSON exclui notas; HTML recebe cinco campos e escapa status. Sem autorização, durabilidade ou teste concorrente naquele baseline.

## Registro

Fontes oficiais estão no relatório correspondente em `docs/`. Mermaid 10.9.3/Chromium produziu as exportações quando aplicável; baselines e hashes registram a versão examinada na época. Documentos de trabalho evoluíram depois desses registros.

Não houve nova execução de pytest, scanner, carga ou exploração nesta revisão. Evidências funcionais reutilizadas pertencem ao Ex. 2.
