# GitHub Actions — Exercício 13

- Execução: https://github.com/leandro-infnet/medical-appointment-api/actions/runs/39531201601
- PR: https://github.com/leandro-infnet/medical-appointment-api/pull/17
- Workflow: Seguranca
- Evento: pull_request
- Branch: feat/ex13-capstone-security-audit
- Commit: c1b98e4b9c386b037dd49f61b4d4cef0a8b1451f
- Resultado remoto: success
- Artefato: relatorios-seguranca
- Relatórios extraídos: github-actions/

## Resultados

- pytest: 233 testes passaram, sem falhas, erros ou skips; um aviso de depreciação.
- Bandit: seis findings LOW, nenhum HIGH e nenhum erro de análise.
- pip-audit: nenhuma vulnerabilidade conhecida retornada.
- Security gate: aprovado, sem motivos de bloqueio.

O exit 1 do Bandit corresponde aos LOW preservados; o gate aplica a política de severidade. Os relatórios remotos complementam `gate-final/`, que registra a execução local. ZAP foi executado separadamente; riscos e bloqueio de produção permanecem no [capstone](../../docs/relatorio-capstone.md).

## Capturas

- [ ] PR #17 com Security gate aprovado.
- [x] [Security gate aprovado na main após o merge do PR #17](github-actions/images/image-02.png), commit `b42c54d`.

Configuração de proteção e demonstração de merge bloqueado estão nas [evidências do Ex. 12](../ex12/github-actions.md).
