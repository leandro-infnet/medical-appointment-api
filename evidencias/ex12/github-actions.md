# GitHub Actions — Exercício 12

- Execução: https://github.com/leandro-infnet/medical-appointment-api/actions/runs/37868988723
- Workflow: Seguranca
- Branch: feat/ex12-devsecops-security-gate
- Commit: df35db5d98ad2e9e173bc3498cc257f28e06cb43
- Resultado remoto: success
- Artefato: relatorios-seguranca
- Relatórios extraídos: github-actions/

## Resultados

- pytest: 214 testes passaram, sem falhas ou testes pulados.
- Bandit: quatro findings LOW, nenhum HIGH.
- pip-audit: nenhuma vulnerabilidade conhecida retornada.
- Security gate: aprovado.

## Proteção da main

Regra criada para `main`, exigindo pull request, branch atualizada
e aprovação do check `Security gate`, sem bypass por administradores.

- [Confirmação da criação](github-actions/images/image-01.png).
- [Configuração da regra](github-actions/images/image-02.png).
- [Check obrigatório e bypass desabilitado](github-actions/images/image-03.png).
- [Security gate aprovado no PR #12](github-actions/images/image-04.png).
- [Security gate aprovado na main após o merge](github-actions/images/image-05.png).

As imagens comprovam a configuração registrada. Não foi demonstrada
uma tentativa de merge com o check reprovado.
