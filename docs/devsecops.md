# DevSecOps — Exercício 12

## Modalidades no SDLC

Ferramentas e limiares abaixo são escolhas de projeto; R19 exige justificar seu lugar no fluxo.

| Tipo | Ferramenta / fase | Motivo | Gate / estado |
| --- | --- | --- | --- |
| Testes | pytest; desenvolvimento e PR | Contratos, autorização e invariantes antes da integração | Falha/erro/skip bloqueia |
| SAST | Bandit; desenvolvimento e PR | AST de `app/` e `scripts/`, sem servidor | HIGH bloqueia, qualquer confiança; LOW/MEDIUM preservados |
| SCA | pip-audit; dependências e PR | Advisories de pacotes instalados, inclusive tooling | Todo finding não triado ou análise incompleta bloqueia |
| DAST | ZAP passivo; integração antes de liberação | Aplicação executando, respostas e tráfego autenticado | Executado no Ex. 13; avaliado no relatório final, fora do gate CI |
| IAST | Datadog Runtime Code Analysis, candidato; homologação | Instrumentação interna correlaciona entrada e execução | Proposta, não instalada; compatibilidade Python 3.14 não verificada |

TestClient não é IAST. Bandit analisa aplicação/scripts, excluindo testes/evidências didáticas; `--ignore-nosec` impede supressões. SCA só tolera skip da distribuição editável do próprio projeto, cujo código passa por SAST/testes. Ferramentas são fixadas no extra `security`; dependências de aplicação têm intervalos, sem lockfile.

## CVSS e impacto de negócio

CVSS v3.1 Base calculado por `cvss` 3.6 em `evidencias/ex12/cvss.json`. Vetor histórico não muda por mitigação posterior; prioridade considera também dados médicos e uso da agenda.

| Finding | Vetor / score | Premissas / impacto | Prioridade |
| --- | --- | --- | --- |
| VUL-001: acesso por objeto histórico | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` — 9,1 | Rede, sem conta/interação; GET/PATCH leem/alteram consultas. C/I altos no serviço; sem efeito A observado | P1; regressão de ownership bloqueia integração |
| VUL-002: headers ausentes | `AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:N/A:N` — 0,0 provisório | Ausência observada, sem clickjacking/sniffing/TLS explorados. C/I/A:N registra falta de impacto demonstrado; não elimina risco de implantação | P2; headers são requisito, portanto regressão bloqueia pytest mesmo com zero provisório |
| VUL-003: login sem quota | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` — 7,4 | Cenário condicional de senha adivinhada permitiria acesso clínico; nenhuma senha/conta foi comprometida no ensaio, nem indisponibilidade medida | P1; mitigada pela quota, com limites de NAT/workers/distribuição |

Ordem: VUL-001, VUL-003, VUL-002. Reavaliar premissas conforme implantação. Scores condicionais não são relatos de exploração; impacto de negócio pode tornar impeditiva uma falha que o scanner classifique abaixo de HIGH.

## Política executável

1. pytest deve ter testes executados e nenhum erro/falha/skip. BOLA, MFA, SQL, XSS, M2M, headers e quotas são regressões obrigatórias, mesmo sem finding de scanner.
2. Bandit HIGH bloqueia por maior impacto potencial; severidade nativa não equivale a CVSS ≥ 7. LOW/MEDIUM permanecem para revisão; dano clínico confirmado exige tratamento independentemente do rótulo.
3. pip-audit bloqueia qualquer advisory até correção/triagem. JSON utilizado não fornece CVSS; score desconhecido não vira baixa severidade. A regra conservadora cabe no projeto sem governança de exceções.
4. Timeout, scanner quebrado, relatório ausente/inválido, pacote inesperadamente pulado, exit code incompatível ou análise vazia bloqueiam. Relatórios anteriores são removidos antes da execução para impedir uso de saída velha.

Cada análise preserva status/logs mesmo se outra falhar; decisão final retorna 1 em reprovação. Sem allowlist de CVE, continue-on-error ou saída forçada de sucesso. Revisão de falso positivo HIGH exige justificativa; não há exceção automática.

## Execução

`.github/workflows/security.yml` usa Python 3.14, contents:read, checkout sem credencial persistida e upload always/erro se ausente. Retenção de artefatos: 14 dias. `scripts/security_gate.py` usa argv fixo, sem shell/segredos de produção; fixtures isolam banco, conta e chave.

```bash
.venv/bin/python -m pip install --upgrade 'pip>=26.2,<27'
.venv/bin/python -m pip install -e '.[dev,security]'
.venv/bin/python scripts/security_gate.py
```

Relatórios transitórios: `reports/security/`. O pip foi atualizado porque a SCA local encontrou advisories em 25.1.1; 26.2.1 passou no novo ensaio. [Evidências locais](../evidencias/ex12/README.md).

## STRIDE → regressão

| Ameaças | Teste / comportamento | Evidência |
| --- | --- | --- |
| TM-001/013 | `test_autorizacao.py`; claim extra de papel/MFA não promove conta comum | JWT/admin e novo caso STRIDE |
| TM-002/003 | `test_regressoes_stride.py`: GET/PATCH/DELETE alheio/inexistente retornam mesmo 404, estado intacto e lista vazia | Três novos casos HTTP |
| TM-004/005 | `test_respostas_templates.py`: campos mínimos e HTML legado escapado | Regressões Ex. 2/9 |
| TM-006/011 | Caso STRIDE de campo extra: 422 sem eco do valor e sem gravação | Quinto novo caso HTTP |
| TM-009/010/015 | `test_persistencia.py`: parâmetros, rollback, reinício e concorrência | SQLite real |
| TM-012/016/008 | `test_hardening.py`: CORS, headers e cotas/recuperação | Relógio controlado e HTTP |
| TM-014 | `test_m2m.py`: parceiro limitado à disponibilidade | Scopes/claims e negativas |
| Gate | `test_security_gate.py`: limiar, relatório inválido/velho, skip e falha de scanner | Mocks de decisão, separados dos scans reais |

Os cinco novos casos HTTP expandem o teste administrativo do Ex. 6. JUnit/logs preservam a execução real; mocks do avaliador não são scanner executado.

## GitHub e bloqueio de merge

[Run aprovado 37868988723](https://github.com/leandro-infnet/medical-appointment-api/actions/runs/37868988723), commit `df35db5d98ad2e9e173bc3498cc257f28e06cb43`: 214 testes, quatro LOW e SCA sem findings. Artefato `relatorios-seguranca` em `evidencias/ex12/github-actions/`.

[Proteção e capturas](../evidencias/ex12/github-actions.md): PR, branch atualizada, Security gate obrigatório e sem bypass administrativo. [PR #15](https://github.com/leandro-infnet/medical-appointment-api/pull/15), [run reprovado](https://github.com/leandro-infnet/medical-appointment-api/actions/runs/37883814260): 214 passaram, um teste deliberado falhou e o merge foi bloqueado. O teste não integra a main. A prova remota é de falha de teste; limites de severidade têm testes próprios e reprovação SCA local preservada.

## Referências

[Bandit](https://bandit.readthedocs.io/en/latest/man/bandit.html), [pip-audit](https://github.com/pypa/pip-audit), [CVSS v3.1](https://www.first.org/cvss/v3.1/specification-document), [branches protegidas](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [ZAP passivo](https://www.zaproxy.org/docs/docker/baseline-scan/), [IAST Python](https://docs.datadoghq.com/security/code_security/iast/setup/compatibility/python/).
