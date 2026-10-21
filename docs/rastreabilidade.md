# Rastreabilidade — Exercícios 1 a 13

Estado consolidado. Os números de testes de cada pasta correspondem ao respectivo baseline; os relatórios históricos permanecem preservados. Catálogo de ameaças/controles/testes em [STRIDE](threat-model.md); decisões e limites finais no [capstone](relatorio-capstone.md).

Caminhos de implementação sem prefixo ficam em `app/`; testes em `tests/`; evidências em `evidencias/`. Os relatórios em `docs/` explicam as decisões de cada etapa.

| Requisito | Ex. | Implementação / arquivo | Teste / verificação | Threat ID | Evidência | Rubrica |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-01: ambiente e CRUD | 1 | main, routes/models/database; pyproject.toml | `test_consultas.py`, Uvicorn/curl | Funcional | ex01: instalação, HTTP e pytest | R01 |
| REQ-02.1: campos públicos | 2 | ConsultaResponse, routes/consultas.py | TEST-02, conjunto de campos | TM-004 | ex02/respostas_http.json | R02 |
| REQ-02.2: justificar saída | 2 | DEC-13, comparação com Ex. 1 | Entidade versus resposta | TM-004 | ex01/HTTP e ex02/JSON | R03 |
| REQ-02.3: agenda/herança | 2 | routes/agenda.py, templates | TEST-03, dia/ordem/UTC/vazio | TM-002/004/005 | ex02: HTML, PNG, pytest | R04 |
| REQ-02.4: escape XSS | 2 | Jinja2 auto-escape | TEST-03, script/imagem como texto | TM-005 | ex02/payloads.json, agenda_xss.html | R04 |
| REQ-03.1: CIA | 3 | cia-dfd.md, CIA-01–08 | Revisão código/ativos/impactos | TM-001–012 | ex03/revisao_documental.md | R05 |
| REQ-03.2: referenciais | 3 | cia-dfd.md, DEC-15 | OWASP/SSDF/CWE → controles | TM-004/005/006 | ex03: relatório/baseline | R05 |
| REQ-03.3: DFD | 3 | dfd-atual.mmd, cia-dfd.md | F-01–10 e TB-01–04 | TM-001–012 | ex03/dfd-atual.svg e PNG | R06 |
| REQ-04.1: misuse cases | 4 | threat-model.md, MU-001–012 | Ator, tentativa, resultado e teste | TM-001–016 | ex04/threat-model-v1.md | R07 |
| REQ-04.2: três componentes | 4 | STRIDE em P-01/02/03 | 18 avaliações S/T/R/I/D/E | TM-001–016 | ex04: snapshot/revisão | R08 |
| REQ-04.3: modelo consolidado | 4 | Ativos, superfícies, CTRL/TEST | IDs/estado/risco residual | TM-001–016 | ex04 e modelo atual | R08 |
| REQ-05.1: partições | 5 | arquitetura-seguranca.md | Responsabilidades/localização | TM pertinentes | ex05: fonte/exports/revisão | R09 |
| REQ-05.2: fluxos | 5 | particoes-seguranca.mmd | Conferência DFD/fronteiras | TM-001–005/011/012 | ex05/particoes-seguranca.svg | R09 |
| REQ-05.3: três eixos | 5 | VD/VI/VF-01–04 | Doze vetores ligados a controles | TM-001–016 | ex05/revisao_documental.md | R09 |
| REQ-06.1: bearer/bcrypt | 6 | auth/passwords.py, dependencies.py | TEST-04, senha/hash/ausência | TM-001/016 | ex06: HTTP/pytest | R10 |
| REQ-06.2: ownership | 6 | auth/policies.py, vínculos no servidor | TEST-07/08/09, acesso cruzado | TM-001–004 | ex06/respostas_http.json | R10/R11 |
| REQ-06.3: JWT | 6 | auth/tokens.py, settings.py | TEST-05, assinatura/datas/claims | TM-013 | ex06: pytest/ambiente | R11 |
| REQ-06.4: MFA | 6 | auth/mfa.py, routes/auth.py | TEST-06/10, desafio/fator/replay | TM-013/016 | ex06: 202/401/200 | R11 |
| REQ-06.5: não admin negado | 6 | test_autorizacao.py | Profissional/recepção → admin 403 | TM-013 | ex06/pytest_output.txt | R11/R22 |
| REQ-06.6: sessão HTML | 6 | Cookie restrito + mesmo validador | TEST-23, flags/escopo/logout | TM-017 | ex06: HTML/HTTP | Complementar |
| REQ-07.1: Client Credentials | 7 | routes/auth.py, auth/m2m.py | Credencial/grant/erros | TM-014/016 | ex07: HTTP e contrato | R12 |
| REQ-07.2: claims/scopes | 7 | tokens.py, SecurityScopes | TEST-05/11, tipos e acesso cruzado | TM-013/014 | ex07/claims_publicas.json | R12 |
| REQ-07.3: disponibilidade | 7 | routes/database/model de disponibilidade | TEST-11, horários e dados mínimos | TM-002/004/009/014 | ex07/respostas_http.json | R12 |
| REQ-08.1: três categorias | 8 | vulnerabilidades.md, VUL-001–003 | Leitura manual e reprodução | TM-002/003/012/016 | ex08: manifesto/JSON | R13 |
| REQ-08.2: BOLA/paciente | 8 | Histórico pré-auth + DEMO-001 | Próprio/alheio; política atual | TM-002/003 | ex08/historico.json, didatico.json | R13/R14, ressalva |
| REQ-08.3: estado anterior | 8 | Snapshots literais e SHA-256 | 37 observações, manifesto | VUL/OBS | ex08/snapshots/, manifesto.json | Base R14–R17 |
| REQ-09.1: middleware/ownership | 9 | auth/middleware.py e policies.py | TEST-04/05/07–11, decode único | TM-001/002/003/014 | ex09: HTTP/pytest | R14 |
| REQ-09.2: entrada estrita | 9 | Schemas, regex e errors.py | TEST-12/22, extra/null/status | TM-006/011 | ex09/resultados.json | R15 |
| REQ-09.3: SQL/HTML | 9 | DEMO-002, Jinja2; SQLModel Ex. 11 | TEST-03/13, antes/depois | TM-005/015 | ex09: SQL isolado/HTML legado | R15/R16, ressalva |
| REQ-09.4: endpoint adicional | 9 | Form /auth/m2m/token estrito | Extra 200 → 422; válido 200 | TM-006/014 | ex09/m2m-antes.json, resultados.json | R15, ressalva |
| REQ-10.1: CORS/headers | 10 | network.py e settings.py | TEST-15, preflight/erros/HTTPS | TM-012 | ex10/respostas_http.json | R17 |
| REQ-10.2: cotas | 10 | RateLimiter por conexão/lifespan | TEST-14, 5/60 e recuperação | TM-016/008 | ex10: 20 tentativas e pytest | R17 |
| REQ-11.1: SQLModel | 11 | models/tabelas.py, database/session.py | TEST-13/16/21, banco real | TM-002/003/009/010/015 | ex11: 181 testes/13 observações | R18 |
| REQ-12.1: SDLC/CVSS | 12 | devsecops.md, DEC-24 | Premissas/vetores/negócio | VUL-001–003 | ex12/cvss.json, antes/depois | R19/R20 |
| REQ-12.2: gate | 12 | .github/workflows/security.yml, scripts/security_gate.py | Limiar/erro/skip/relatório velho | CTRL-07/08/11 | ex12/github-actions.md; PR #15 | R21 |
| REQ-12.3: expansão STRIDE | 12 | test_regressoes_stride.py | Cinco novos casos HTTP | TM-002/003/006/011/013 | ex12: JUnit/pytest | R22 |
| REQ-13.1: ZAP e decisão | 13 | scripts/zap_passivo.py, relatorio-capstone.md | 25 requisições por scan | TM-001/004/005/012/014 | ex13/zap-antes/, zap-depois/ | R23 |
| REQ-13.2: mocking/OpenAPI | 13 | test_capstone.py, auditoria-openapi.md | Entrada/ownership/login/scopes/schema | TM-002/003/006/011/013/014 | ex13/gate-final/, OpenAPI | R24 |

## Resultado consolidado e limites

- Gate final Ex. 13: 233 testes aprovados; seis LOW Bandit; SCA sem advisories retornados.
- ZAP: 15→14 instâncias; CSP agenda corrigida. HIGH de Basic/HTTP e demais riscos impedem produção.
- R13/R14/R15/R16: paciente/histórico/SQL isolados e endpoint adicional mantêm ressalvas acadêmicas. SQLModel real é verificado; não transforma o ANTES didático em falha histórica do produto.
- TLS/browser reais, MFA real, auditoria persistente, backup/restore e capacidade não estão demonstrados. IAST permanece proposto.
- Vídeo e ZIP final continuam itens de entrega. [Relatório final e decisão](relatorio-capstone.md).
