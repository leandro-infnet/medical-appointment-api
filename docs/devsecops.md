# Exercício 12 — Pipeline DevSecOps e security gate

O pipeline verifica a aplicação SQLModel/SQLite integrada sem publicar ou fazer deploy. Entregas: posicionamento de SAST/SCA/DAST/IAST no SDLC (R19), priorização CVSS/negócio (R20), gate em GitHub Actions (R21) e expansão dos testes derivados do STRIDE (R22). As escolhas abaixo são recomendações de engenharia adotadas para o escopo acadêmico, não ferramentas adicionais impostas pela disciplina.

## Análises no SDLC

| Tipo | Ferramenta | Fase e justificativa | Bloqueio/estado |
| --- | --- | --- | --- |
| Testes | pytest | Desenvolvimento e cada PR; contratos, autorização e invariantes são verificados antes da integração | Obrigatório: qualquer falha, erro ou teste pulado bloqueia |
| SAST | Bandit | Desenvolvimento e PR; AST de `app/` e `scripts/`, sem precisar subir servidor | HIGH bloqueia com qualquer confiança; todos os níveis ficam no relatório; erros/relatório inválido também bloqueiam |
| SCA | pip-audit | Instalação/alteração de dependências e cada PR; consulta advisories de todas as distribuições instaladas no ambiente CI, incluindo ferramentas | Qualquer finding não triado bloqueia; ausência de score não é baixa severidade; análise incompleta bloqueia |
| DAST | OWASP ZAP passivo | Integração/homologação antes de liberação, no Ex. 13; depende da aplicação executando e tráfego com autenticação, não só compilação | Não executado neste incremento; será incorporado à avaliação de liberação, sem resultado verde fictício |
| IAST | Datadog Runtime Code Analysis, candidato | Integração/homologação instrumentada durante tráfego/testes; relaciona entradas com execução interna | Apenas proposta: agente/serviço/compatibilidade com Python 3.14 não foram verificados; não está no gate executável |

DAST observa respostas; IAST requer instrumentação interna. Executar pytest com TestClient não é IAST, nem substitui ZAP. Datadog é candidato por documentar suporte Python/FastAPI; não foi instalado nem configurado, e não serão enviados dados a serviço externo. A avaliação dessa modalidade atende ao posicionamento no SDLC; não se alega quatro scanners executados.

SAST exclui testes/evidências deliberadamente didáticos e fontes históricas vulneráveis. O escopo executável é `app/` e `scripts/`, com `--ignore-nosec`, sem baseline/supressão para ocultar findings. SCA omite somente a própria distribuição editável `medical-appointment-api` (fonte analisada por SAST/pytest); todos os outros pacotes instalados devem ser analisados. O runner rejeita skips de outras dependências. Versões de ferramentas são fixadas no extra `security`; dependências de aplicação ainda usam intervalos, e o relatório guarda as versões efetivamente resolvidas. Isso não equivale a lockfile ou build bit a bit reproduzível.

## CVSS histórico e impacto de negócio

Adotado **CVSS v3.1 Base**, com vetores completos, calculados pela biblioteca `cvss` 3.6 e registrados em `evidencias/ex12/cvss.json`. O score expressa o cenário técnico modelado; não é prova de exploração nem previsão de probabilidade. Mitigações posteriores não alteram o vetor histórico. Impacto de negócio e prioridade são registrados separadamente.

| Finding | Vetor CVSS v3.1 / score | Premissas e impacto | Prioridade / estado |
| --- | --- | --- | --- |
| VUL-001 — acesso por objeto sem autorização no histórico | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` — **9,1** | Acesso por rede, sem conta nem interação, GET/PATCH permitem ler/alterar consultas. C/I altos modelam leitura/alteração da agenda e informações clínicas do serviço; A não afetada neste ensaio, escopo inalterado. Evidência usa dados fictícios, sem prontuário real | P1: confidencialidade/integridade médica impedem aceitar regressão. Mitigada Ex. 6/9; TEST-07/08/09/Ex. 12 bloqueiam retorno |
| VUL-002 — hardening de navegador ausente | `AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:N/A:N` — **0,0 provisório** | Ausência de headers foi observada, **clickjacking/sniffing/TLS não foram explorados**. A agenda atual é somente leitura; não há ação HTML demonstrada que altere consultas por enquadramento nem leitura cross-origin comprovada. C/I/A:N delimita o resultado observado, sem inventar impacto. O vetor registra a superfície/interação potencial; sem impacto Base resulta em zero. Não significa ausência de risco de implantação; reavaliar com browser/TLS/UI reais. HSTS ausente em HTTP local não é vulnerabilidade isolada | P2 técnico, mas headers são requisito e sua regressão bloqueia pytest. Mitigada Ex. 10 no escopo local; efeito em navegador/TLS ainda pendente |
| VUL-003 — login sem quota | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` — **7,4** | Cenário de adivinhação bem-sucedida requer condições adicionais de senha (AC:H); sem conta inicial/ação da vítima, comprometer profissional permitiria ler/alterar consultas. **Não houve senha descoberta/tomada de conta**; somente repetição sem throttling foi observada. Não atribuir A:H sem medir indisponibilidade | P1 pelo potencial acesso clínico. Mitigada Ex. 10; testes verificam limiar, IP, grupo credenciais e recuperação. Distribuição de IPs/workers permanece residual |

VUL-002 usa score provisório limitado ao que foi observado, sem impacto demonstrado; VUL-003 usa avaliação condicional de risco, não score de um exploit confirmado. Se o contexto real de implantação diferir, reavaliar as métricas; não transformar uma ausência de controle automaticamente em dano observado. Risco acadêmico de histórico/paciente didático permanece explícito em `vulnerabilidades.md`.

A ordem de tratamento é VUL-001, VUL-003, VUL-002 pela gravidade modelada; requisitos e impacto podem elevar a urgência de VUL-002 mesmo com score médio. Dados médicos e mutação de agenda justificam bloquear ownership/auth independentemente de score. Não se afirma conformidade LGPD ou sistema seguro por passar no gate.

## Política executável e justificativa

1. **pytest:** todos os testes obrigatórios passam, nenhum é pulado, JUnit contém testes. Isso inclui autorização administrativa iniciada Ex. 6, BOLA, JWT/M2M, SQL, XSS, headers, quota e integridade. Regressões de VUL-001/003 são impeditivas mesmo que um scanner não as encontre.
2. **Bandit:** bloquear HIGH, com qualquer confiança; preservar LOW/MEDIUM para inspeção. HIGH é severidade nativa, **não é conversão para CVSS ≥ 7**. Limiar escolhido para padrões de código com maior impacto, complementado pelos testes de negócio. Não exclui manualmente um finding confirmado que exponha dados clínicos apenas por receber MEDIUM.
3. **pip-audit:** bloquear toda vulnerabilidade conhecida encontrada até correção/triagem. A ferramenta não entrega score CVSS no JSON utilizado; não inferir severidade de ID, nome ou score ausente. A escolha é conservadora para dependências em um projeto pequeno, sem governança de exceções. Findings de tooling também devem ser tratados.
4. **Falha operacional:** scanner quebrado/timeout, JSON/XML inválido/ausente, erro de leitura, pacote inesperadamente pulado, exit code incompatível ou ausência de testes/análise bloqueiam. O runner remove apenas relatórios próprios antigos antes de executar para impedir que um scan falho use um JSON anterior.

Não há allowlist de CVE, `continue-on-error`, `|| true` ou `--exit-zero`. Exit 1 do scanner pode significar findings: o runner examina o relatório, preserva o status original e aplica a política; não o transforma cegamente em sucesso. Cada análise roda mesmo se outra falhar para preservar evidências, mas o processo final retorna **1** quando qualquer condição de bloqueio se aplica. Não há exceções automáticas: falso positivo HIGH exige revisão da política/finding e evidência antes do merge, nunca desligar o scanner inteiro.

Essa combinação liga o gate ao histórico: acesso indevido a dados/alterações bloqueia testes; login sem limite bloqueia regressão; falta de headers obrigatórios também bloqueia; padrões genéricos de código e advisories recebem análises específicas. Um pipeline verde é necessário para integração, mas insuficiente para liberar produção: ZAP, riscos residuais, TLS e auditoria final continuam no Ex. 13.

## Implementação e reprodução

- `.github/workflows/security.yml`: push em main/branches do projeto, PR para main e disparo manual; Python 3.14, token com `contents: read`, checkout sem credencial persistida, artefatos preservados com `if: always()` e falha quando ausentes.
- `scripts/security_gate.py`: roda pytest/Bandit/pip-audit, escreve logs, JUnit, JSON e `gate.json`, sem shell ou credenciais de produção. Timeout de scanner/testes impede job preso, não representa meta de desempenho da API.
- `pyproject.toml`: extra `security` fixa ferramentas. O workflow atualiza pip antes da instalação porque a análise encontrou advisories na ferramenta antiga do ambiente local.
- Testes usam banco/cadastro/chave temporários pela fixture; CI não precisa de secrets GitHub ou `.env` real. Artefatos retidos por 14 dias são evidência temporária de desenvolvimento, não política de retenção de saúde.

```bash
.venv/bin/python -m pip install --upgrade 'pip>=26.2,<27'
.venv/bin/python -m pip install -e '.[dev,security]'
.venv/bin/python scripts/security_gate.py
```

Relatórios transitórios ficam em `reports/security/`, ignorado pelo Git; copiar somente saídas revisadas para evidências. Configurações que enfraqueçam o contrato para ficar verde não fazem parte dessa sequência.

## Matriz STRIDE → teste → evidência

| Threat ID | Vetor / endpoint | Regressão / arquivo | Evidência |
| --- | --- | --- | --- |
| TM-001/013 | Identidade/JWT e admin | `test_autorizacao.py`, novo `test_tm013_claim_papel_e_mfa_nao_substituem_papel_confiavel` | JUnit/pytest; mesmo token assinado controlado com claim de papel extra continua sem privilégio |
| TM-002/003 | BOLA GET/PATCH/DELETE/lista | Novos três casos `test_tm002_tm003_acesso_cruzado_mesmo_erro_sem_efeito` + controles Ex. 6 | Recurso próprio permanece intacto; alheio/inexistente mesmo 404; lista alheia vazia |
| TM-004/005 | Dados internos e XSS HTML | `test_respostas_templates.py` | Banco/response model e projeção legada explicitamente mockada; sem enfraquecer CHECK |
| TM-006/011 | Entrada extra / erro sensível | Novo `test_tm006_tm011_erro_nao_grava_nem_repete_campo_extra` + entrada/saída | 422, marcador ausente na resposta e nenhuma linha gravada |
| TM-009/010/015 | Concorrência, durabilidade, SQL | `test_persistencia.py` | SQLite real, parâmetros/rollback/reinício; Ex. 11 preservado e regressão no JUnit atual |
| TM-012 | CORS e headers | `test_hardening.py` | Origem permitida/negada; autenticação/erros/HTTPS em processo |
| TM-014 | M2M scope/claims / rotas humanas | `test_m2m.py` | Laboratório continua limitado à disponibilidade |
| TM-016/008 | Credenciais e abuso | `test_hardening.py` | 5/60, recuperação com relógio controlado, X-Forwarded-For não aumenta cota |
| Gate | Aprovação/bloqueio/indisponibilidade | `test_security_gate.py` | Limiar HIGH, desconhecido/incompleto, SCA sem score, skip, scanner falho, relatório antigo/ausente/inválido e saída final |

Os cinco novos casos HTTP expandem o teste administrativo Ex. 6 para outros vetores, além de reutilizar a suíte existente. Testes do avaliador usam relatórios fictícios e mocks identificados; não são evidência de scanner executado. Os relatórios reais são preservados separadamente.

## GitHub, merge e pendências

**Não houve push, run remoto ou alteração de proteção da branch nesta implementação local.** Depois do push/PR, guardar URL/ID do run e artefato `relatorios-seguranca`. No GitHub, configurar proteção/ruleset de `main` com **Require status checks to pass**, exigindo o check **Security gate** que aparecer após a primeira execução. Verificar o nome efetivo e exigir branch atualizada; considerar restrição de bypass para administradores. Se plano/permissão impedir, registrar a limitação para R21.

Sem essa configuração externa, falhar o workflow **não impede merge**. Não há print/run/merge bloqueado inventado; configuração e evidências remotas continuam pendentes. Não criar vulnerabilidade na API para provar vermelho. Os testes unitários provam o avaliador e a SCA real do pip antigo prova bloqueio local; isso não é run GitHub Actions.

## Referências primárias

- [Bandit: parâmetros e formato de relatório](https://bandit.readthedocs.io/en/latest/man/bandit.html).
- [pip-audit: auditoria de ambiente e limites](https://github.com/pypa/pip-audit).
- [FIRST: CVSS v3.1](https://www.first.org/cvss/v3.1/specification-document).
- [GitHub: required status checks e proteção](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- [ZAP baseline/passive scan](https://www.zaproxy.org/docs/docker/baseline-scan/).
- [Datadog: compatibilidade Python para IAST](https://docs.datadoghq.com/security/code_security/iast/setup/compatibility/python/).
