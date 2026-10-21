# Relatório final de segurança e rastreabilidade

Data da auditoria: 19/10/2026. Aplicação FastAPI integrada com SQLModel/SQLite, autenticação humana e M2M, autorização por papel/vínculo/recurso, validação e hardening. Este relatório consolida as decisões dos exercícios; não constitui certificação ou autorização de deploy.

## Resultado e decisão de liberação

**Liberação para produção bloqueada.** O experimento local HTTP permitiu ao ZAP identificar Basic sem proteção TLS no endpoint M2M. JWT, cookie e senha humana também exigem transporte protegido, mesmo que o scanner não tenha emitido um alerta específico para cada um. HSTS não cifra HTTP nem substitui TLS.

A implementação pode ser demonstrada academicamente em loopback com dados fictícios. Para produção, verificar TLS e cadeia de confiança no ponto de terminação, encaminhamento de esquema somente por proxy confiável e cookie Secure; repetir tráfego autenticado no endereço HTTPS real. Também faltam controles operacionais de auditoria, recuperação e gestão de identidades descritos abaixo. Nenhum deploy foi realizado.

## Método e evidências

1. Revisão dos contratos, políticas e testes existentes; preservação das evidências anteriores.
2. Acréscimo de testes unitários com `unittest.mock` para criação, entradas inválidas, ownership, negação administrativa, login sem emissão indevida e scopes M2M; testes HTTP do schema/cache/CSP.
3. Auditoria do OpenAPI, comparação com respostas reais e correção de contratos de acesso/cookie.
4. ZAP 2.17.0 oficial em `mode=safe`, scanners ativos desabilitados, sem spider: 25 requisições controladas em banco temporário por execução.
5. Correção de CSP na agenda e `no-store` nas respostas protegidas; repetição do mesmo tráfego.
6. Suíte completa e gate de pytest/Bandit/pip-audit; preservação de logs, JSON e JUnit em `evidencias/ex13/`.

[Inventário e comandos das evidências](../evidencias/ex13/README.md). [Auditoria OpenAPI](auditoria-openapi.md). O scan observou requisições HTTP legítimas e negativas controladas; não realizou exploração ativa, navegador, concorrência, teste de capacidade ou pentest completo. A comparação antes/depois usa os diretórios `zap-antes/` e `zap-depois/`. As credenciais eram efêmeras e foram removidas dos relatórios; a sanitização não remove IDs/severidades/URLs dos alertas.

## Findings do ZAP e tratamento

Referencial de classificação deste relatório: **OWASP Top 10:2021**, para manter continuidade com o histórico. O ZAP também emite tags de outras edições; elas não são intercambiadas silenciosamente. BOLA é API1:2023 no OWASP API Security Top 10 e foi correlacionada a A01:2021 no histórico.

| Finding / regra | Antes → depois (instâncias) | Categoria / ameaça | Análise, controle e evidência |
| --- | --- | --- | --- |
| ZAP-01 / 10038 — CSP ausente, Medium | 2 → 1 | A05:2021; TM-005/012 | Agenda corrigida em `app/network.py`: `default-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'`, `form-action 'self'`. Template atual não usa scripts/styles externos. Teste `test_respostas_clinicas_nao_permanecem_em_cache` e scan depois confirmam header/ausência do alerta na agenda. `/docs` permanece sem CSP; não alegar correção global |
| ZAP-02 / 90003 — recursos sem SRI, Medium | 2 → 2 | A08:2021; TM-012 | Swagger padrão usa CSS/JS externos sem integridade; nenhum comprometimento de CDN foi observado. Pendência: servir assets locais fixados com CSP compatível ou retirar docs da implantação pública. Sem alteração desses assets neste capstone |
| ZAP-03 / 10017 — JS externo, Low | 1 → 1 | A08:2021, relacionado a ZAP-02 | Inclusão de JS do CDN no Swagger; é dependência de confiança, não prova de XSS. `/docs` restrito ao uso local na demonstração; tratar antes da exposição pública |
| ZAP-04 / 10105 — credenciais capturadas, High | 1 → 1 | A02:2021 (transporte), relacionado a A07:2021; TM-001/014 | Basic decodificável sobre HTTP local em `/auth/m2m/token`. O relatório sanitizado preserva o diagnóstico sem senha. Não trocar Client Credentials/Basic exigidos pelo contrato: corrigir canal com TLS real. **Bloqueia produção**; não corrigido por bcrypt/JWT/HSTS |
| ZAP-I01 / 10111 — autenticação identificada, Informational | 3 → 3 | Sem vulnerabilidade OWASP confirmada | Três logins humanos observados. Senhas fictícias, bcrypt, tokens expirantes e MFA admin; identificação da superfície não demonstra bypass |
| ZAP-I02 / 10112 — sessão identificada, Informational | 4 → 4 | Sem vulnerabilidade OWASP confirmada | Tokens/cookie identificados nas respostas; `HttpOnly`, escopo de path e políticas testados. Secure foi desabilitado explicitamente só para HTTP local; não aceitar esse parâmetro em produção |
| ZAP-I03 / 10109 — aplicação moderna, Informational | 1 → 1 | Não aplicável | Swagger com JavaScript; o experimento não abriu navegador nem executou JS externo |
| ZAP-I04 / 10031 — atributo controlável / potencial XSS, Informational | 1 → 1 | TM-005; possível A03:2021, **não confirmada** | Parâmetro `dia` participa de atributo HTML; é validado como `date` e escapado pelo Jinja2. Não foi observada execução de script. Testes existentes verificam XSS persistido em projeção legada; entrada de data inválida é rejeitada |

Totais: **15 instâncias antes, 14 depois**, oito regras distintas em cada scan. O delta corresponde à agenda com CSP. Não converter instâncias repetidas em vulnerabilidades distintas. Ausência de alerta para SQL/ownership/cache não prova ausência de falha nesses controles.

## Revisão manual e correções adicionais

| ID | Localização / causa | Correção / teste | Estado |
| --- | --- | --- | --- |
| OA-01 | Agenda aceitava cookie no middleware, schema anunciava somente bearer | `app/auth/dependencies.py`: scheme `AgendaCookie` como alternativa; `test_openapi_agenda_aceita_bearer_ou_cookie` | Corrigido; validador JWT central preservado |
| OA-02 | Respostas 401/403 omitidas para agenda, admin e sessão | Routers/decorators documentados; três casos de `test_openapi_documenta_erros_de_acesso_reais` | Corrigido; falta de documentação não foi bypass |
| MAN-01 | GET JSON de consultas não estabelecia proibição explícita de cache | `app/network.py` centraliza `Cache-Control: no-store` nas respostas protegidas, inclusive erros; teste HTTP e `trafego.json` | Corrigido como defesa de confidencialidade, sem vazamento comprovado |
| OA-03 | PATCH opcional admite null no schema, mas validador rejeita em campos obrigatórios | Cliente deve omitir campo; comportamento 422 coberto pela suíte | Limitação de contrato documentada, sem aceitação indevida de null |

## Rastreabilidade do threat model aos testes finais

| Threat ID | Finding / risco | Controle / implementação | Teste / ferramenta | Evidência |
| --- | --- | --- | --- | --- |
| TM-001/013 | Identidade falsa / promoção administrativa | JWT central, cadastro confiável, MFA simulado e papéis | `test_autorizacao.py`, `test_regressoes_stride.py`, unidade de login em `test_capstone.py` | JUnit final; tráfego MFA/admin |
| TM-002/003 | VUL-001 histórica / BOLA | `policies.py`, filtros e autorização antes de mutação | GET/PATCH/DELETE cruzados; unidades com banco mockado retornando recurso alheio/ausente | Ex. 6/9/12 e gate final; mocks não substituem banco real |
| TM-004 | Exposição de campos internos / cache | response models, projeção HTML e no-store | `test_respostas_templates.py`, teste de contrato/schema/cache | Ex. 2 e trafego.json final |
| TM-005/012 | ZAP-01/I04 / XSS | Jinja2 auto-escape, data/status validados e CSP agenda | Testes XSS legados com mock explícito; data inválida; teste CSP e ZAP | Ex. 2/9, alertas antes/depois |
| TM-006/011 | Entrada indevida / erro com dado sensível | Pydantic extra forbid, handler mínimo | Unidade de validação sem chamada ao banco; HTTP extra/limites/null | Gate final e Ex. 9/12 |
| TM-007 | Repúdio / falta de auditoria persistente | Sem solução completa de trilha persistente | Revisão documental; não há teste alegado de controle inexistente | Risco residual abaixo |
| TM-009/010/015 | Corrida, perda de dados e SQL injection | SQLModel parametrizado, sessão/transação e bloqueio de escrita SQLite | `test_persistencia.py`: parâmetros/constraints/rollback/reinício/concorrência | Ex. 11 e suíte final |
| TM-012 | VUL-002, ZAP-01/02/03 e OA-01/02 | CORS explícito, headers, CSP agenda e contratos | Hardening HTTP, OpenAPI e ZAP | Ex. 10/13; TLS/CDN ainda residuais |
| TM-014 | Claims/scopes M2M / ZAP-04 | Audience/token_use distintos, Basic e scope mínimo | `test_m2m.py`; unidade de scopes; tráfego humano/M2M cruzado | Ex. 7 e gate/tráfego finais |
| TM-008/016 | VUL-003 / abuso e indisponibilidade | Quotas diferenciadas e rejeição de proxy não confiável | `test_hardening.py`, relógio controlado | Ex. 10 e gate final; não é teste de DoS |
| TM-017 | Sessão/cookie | HttpOnly/SameSite/path, expiração e identidade central | Suíte de autorização/M2M e tráfego de sessão | Ex. 6/7; Secure de produção requer TLS |

O teste de criação inicial do Ex. 1 permanece na suíte integrada. A unidade de criação do capstone mocka apenas a escrita e verifica delegação; a unidade de entrada inválida demonstra que o modelo rejeita antes da operação; a unidade de vínculo proibido comprova ausência de escrita. Outras unidades verificam recurso carregado do banco, papel administrativo, credenciais incorretas sem emitir token e scope M2M. Mocks não comprovam transações, SQL, middleware ou serialização: as suítes HTTP/SQLite anteriores permanecem necessárias.

## Resultados do gate e triagem

A execução intermediária preservada em `evidencias/ex13/gate/` teve **229 testes aprovados**, seis LOW no Bandit e nenhum advisory retornado pelo pip-audit. O resultado final, após ampliar as unidades de login/scopes e organizar o script de reprodução, está em `gate-final/`; **233 testes aprovados**, dois avisos de depreciação, seis LOW Bandit, nenhum advisory SCA e decisão aprovada do gate. O log e JUnit desse diretório são a referência do fechamento. Após um ajuste de tipagem para usar formulário FastAPI real no teste de login e checar presença do cookie no executor, os 19 casos de `tests/test_capstone.py` passaram novamente.

Os quatro LOW históricos continuam justificados em `evidencias/ex12/README.md`. Os dois LOW adicionais são B404/B603 em `scripts/zap_passivo.py`: subprocess necessário para iniciar Uvicorn, argv fixo sem shell, loopback e ambiente fictício temporário; nenhum argumento vem de requisição da API. São mantidos no relatório, sem supressão. A ferramenta não identifica vulnerabilidades de domínio apenas por analisar AST.

**Gate CI aprovado não libera deploy:** ele verifica pytest/SAST/SCA. ZAP é executado separadamente e seu HIGH impede a recomendação de produção neste relatório. O bloqueio remoto do check obrigatório foi demonstrado no [PR #15](https://github.com/leandro-infnet/medical-appointment-api/pull/15), com teste deliberadamente falho fora da main, não com exploração da aplicação. [Evidência de merge bloqueado](../evidencias/ex12/github-actions-failed/images/image-06.png).

## Riscos residuais e critérios de reavaliação

| Risco | Aceitação contextual / decisão | Condição para reavaliar |
| --- | --- | --- |
| Transporte HTTP / ZAP-04 | Aceito apenas no experimento efêmero em loopback com dados fictícios. **Bloqueia produção** | TLS válido, proxy confiável, Secure ativo e repetição de tráfego/scan HTTPS |
| Swagger externo sem CSP/SRI | Aceito para documentação local; não aprovado para exposição pública | Remover docs públicas ou servir assets fixados/localmente com política adequada; scan/browser |
| Sem trilha de auditoria persistente TM-007 | Limitação de protótipo; **bloqueia operação clínica real** por falta de investigação de ações | Auditoria mínima de ator/ação/alvo/instante/resultado, sem dados clínicos, com acesso/retenção e testes |
| MFA simulado / cadastro local e revogação limitada | Não equivale a identidade de produção; **bloqueia uso clínico real** | Identidade/MFA real, ciclo de vida/revogação e procedimentos testados |
| Quotas em memória, um processo, NAT/distribuição | Suficiente para demonstrar regra local; não prova resistência a DoS | Topologia definida e teste contextual, armazenamento compartilhado quando necessário |
| SQLite, backup/restore e evolução de schema | Concorrência local testada não prova recuperação operacional; **bloqueia dados reais sem procedimentos** | Backup/restauração e migração ensaiados, permissões e operação definidas |
| OA-03 / null no schema PATCH | Aceitável para cliente acadêmico instruído a omitir campos | Alinhar schema/comportamento antes de distribuição de SDK/integração externa |
| Cobertura limitada do scan passivo | Não equivale a pentest, TLS ou navegador real | Avaliar ambiente implantável e ampliar verificação conforme risco |
| Experimentos dos Ex. 8/9 | Aceitação acadêmica do paciente didático, histórico e SQL isolado não é garantida | Avaliação docente; manter a distinção entre achado real e experimento |

## Conferência da rubrica

A tabela aponta evidência disponível, não atribui nota ou aprovação acadêmica. Relatórios por exercício permanecem necessários para detalhes.

| Rubrica | Onde demonstrar | Evidência / ressalva |
| --- | --- | --- |
| R01 | Fundação modular, APIRouter e pytest | Ex. 1, `test_consultas.py`, regressão final |
| R02–R03 | Response models e minimização justificada | Ex. 2, decisões DEC-13, testes de resposta |
| R04 | Agenda diária, herança e escape Jinja2 | Ex. 2/9, HTML e testes de XSS |
| R05–R06 | CIA, referenciais, DFD/fronteiras | `cia-dfd.md`, `dfd-atual.mmd`, Ex. 3 |
| R07–R08 | Misuse cases e STRIDE | `threat-model.md`, Ex. 4 |
| R09 | Partições e vetores de arquitetura | `arquitetura-seguranca.md`, Ex. 5 |
| R10–R11 | Auth, ownership, MFA e negação administrativa | `autenticacao-autorizacao.md`, Ex. 6 e suíte final |
| R12 | M2M, scopes e claims | `integracao-m2m.md`, Ex. 7 e testes |
| R13–R14 | Revisão de três categorias e BOLA | `vulnerabilidades.md`, Ex. 8/9; aceitação dos experimentos permanece ressalvada |
| R15–R16 | Validação, SQL e XSS | `correcoes-entrada-saida.md`, SQLModel real Ex. 11; antes/depois SQL isolado é didático |
| R17 | CORS, headers e rate limiting | `hardening.md`, Ex. 10; TLS real não comprovado |
| R18 | SQLModel parametrizado e BaseSettings | `persistencia.md`, Ex. 11; banco SQLite sem senha; `.env` não entregue |
| R19–R20 | SDLC e priorização CVSS/negócio | `devsecops.md`, `evidencias/ex12/cvss.json` |
| R21 | Gate, execução e merge bloqueado | Ex. 12, PR #15, relatórios e screenshot; falha controlada de teste |
| R22 | Testes derivados do STRIDE | `test_regressoes_stride.py`, matriz DevSecOps, gate final |
| R23 | ZAP, OWASP, correções e decisão residual | Este relatório, scans antes/depois; produção bloqueada |
| R24 | Unidades com mocking e auditoria OpenAPI | `test_capstone.py`, `auditoria-openapi.md`, JUnit final |

## Entrega ainda necessária

- [ ] Commit/PR e run remoto das alterações finais aprovados; isso não remove bloqueios de deploy.
- [ ] Vídeo de até cinco minutos, no YouTube não listado, com link real na entrega.
- [ ] ZIP final revisado, sem credenciais, banco/cadastro real, `.env`, ambiente virtual ou caches.

O link de pasta Drive presente no README é local de apoio ao vídeo; não substitui o requisito de publicação no YouTube não listado. Não foi gerado novo ZIP nem publicado vídeo neste capstone.

## Referências

- [ZAP: baseline e análise passiva](https://www.zaproxy.org/docs/docker/baseline-scan/).
- [ZAP: regra 10105](https://www.zaproxy.org/docs/alerts/10105/).
- [OWASP Top 10:2021](https://owasp.org/Top10/2021/).
- [OWASP API Security Top 10:2023 — BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/).
