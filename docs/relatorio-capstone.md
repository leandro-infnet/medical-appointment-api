# Capstone — auditoria final

Auditoria local: FastAPI integrada com autenticação, autorização, validação, headers e SQLModel/SQLite. **Produção bloqueada** pelos riscos de transporte e operação abaixo. A demonstração usa somente loopback e dados fictícios.

## Método e resultados

- Testes unitários com mocking para criação, entradas inválidas, ownership, papel, login e scopes; complementam os testes HTTP/SQLite anteriores.
- Auditoria de `/openapi.json` contra respostas reais: cookie da agenda e erros 401/403 corrigidos; diferenças residuais documentadas em [OpenAPI](auditoria-openapi.md).
- ZAP 2.17.0, mode safe, scanners ativos desabilitados e sem spider. Cada scan passou 25 requisições pelo proxy, incluindo login, MFA, CRUD, agenda e M2M. Banco/contas temporários; relatórios sanitizados para remover segredos.
- Gate final: **233 testes aprovados**, dois avisos de depreciação, seis LOW Bandit e SCA sem advisories retornados. Após ajustes nos testes, os 19 casos de capstone passaram novamente.

[Comandos, versão/digest, alcance e artefatos](../evidencias/ex13/README.md). Scans antes/depois em `zap-antes/` e `zap-depois/`; decisão/logs/JUnit em `gate-final/`. O scan passivo não fez exploração ativa, navegador, TLS ou teste de capacidade.

## Findings e tratamento

Classificação: OWASP Top 10:2021, mantendo o referencial do histórico. Tags de outras edições emitidas pelo ZAP não mudam esse recorte. BOLA também corresponde a API1:2023, lista separada.

| ID / regra / severidade | Antes → depois | OWASP / ameaça | Tratamento e verificação |
| --- | --- | --- | --- |
| ZAP-01 / 10038 / Medium — CSP ausente | 2 → 1 | A05; TM-005/012 | Agenda corrigida em `app/network.py`: default-src none, base-uri none, frame-ancestors none e form-action self. Teste HTTP e scan confirmam correção na agenda. `/docs` permanece sem CSP |
| ZAP-02 / 90003 / Medium — SRI ausente | 2 → 2 | A08; TM-012 | CSS/JS externos do Swagger sem integridade. Pendente servir assets locais fixados/CSP ou remover docs públicas; sem comprometimento de CDN observado |
| ZAP-03 / 10017 / Low — JS externo | 1 → 1 | A08; relacionado a ZAP-02 | Dependência de confiança do Swagger; uso local, exposição pública pendente |
| ZAP-04 / 10105 / High — credencial capturada | 1 → 1 | A02, relacionado a A07; TM-001/014 | Basic sobre HTTP em `/auth/m2m/token`. TLS real é a correção necessária; bcrypt/JWT/HSTS não cifram esse canal. Bloqueia produção |
| ZAP-I01 / 10111 / Informational | 3 → 3 | Superfície de autenticação | Três logins identificados; sem bypass demonstrado |
| ZAP-I02 / 10112 / Informational | 4 → 4 | Superfície de sessão | Emissão de token/cookie identificada. Flags testadas; Secure=false somente no HTTP local |
| ZAP-I03 / 10109 / Informational | 1 → 1 | Não aplicável | Swagger com JS; navegador/CDN não executados no experimento |
| ZAP-I04 / 10031 / Informational — potencial XSS | 1 → 1 | Possível A03 não confirmada; TM-005 | Dia participa de atributo HTML, mas é validado como date e escapado; sem script executado |

Totais: 15→14 instâncias, oito regras distintas. A redução corresponde à CSP da agenda. Alertas informativos não são automaticamente vulnerabilidades; repetição de instâncias não cria categorias novas.

## Revisão manual e rastreabilidade

| Finding / ameaça | Controle / arquivo | Teste / evidência |
| --- | --- | --- |
| OA-01 | Cookie anunciado como alternativa bearer em `auth/dependencies.py` | `test_openapi_agenda_aceita_bearer_ou_cookie`; snapshots OpenAPI |
| OA-02 | 401/403 declarados em agenda, admin e sessão | Três casos `test_openapi_documenta_erros_de_acesso_reais` |
| MAN-01 / TM-004 | No-store central em respostas protegidas, inclusive JSON de consultas | `test_respostas_clinicas_nao_permanecem_em_cache`; trafego.json |
| TM-001/013 | JWT, cadastro confiável, papéis/MFA | Autorização/STRIDE; unidade de login sem emissão indevida |
| TM-002/003 / VUL-001 | Política central, filtros e vínculo antes da escrita | GET/PATCH/DELETE cruzados; unidades com recurso alheio/ausente mockado |
| TM-004/005/006/011 | Response model, auto-escape, extra forbid e erro mínimo | Respostas/templates/entrada; unidade inválida sem escrita |
| TM-009/010/015 | SQLModel parametrizado, FK/CHECK e transação | Persistência real: parâmetros, rollback, reinício e concorrência |
| TM-012/016/008 | CORS, headers e cotas | Hardening com relógio controlado; ZAP antes/depois |
| TM-014/017 | Scopes/claims M2M e cookie exclusivo da agenda | Testes M2M/cookie, unidades de scopes e tráfego cruzado |

Arquivos de testes em `tests/`; saídas finais em `evidencias/ex13/`. O [catálogo STRIDE](threat-model.md) mantém todos os TM/CTRL/TEST, e a [matriz central](rastreabilidade.md) relaciona os exercícios à rubrica R01–R24.

A criação inicial do Ex. 1 continua na suíte. A unidade de criação mocka a escrita e confirma delegação; vínculo/entrada negados não escrevem. Mocks não comprovam transação, SQL, middleware ou serialização, que permanecem nos testes integrados.

## Gate e riscos residuais

Os seis LOW Bandit foram mantidos: B106 nos discriminadores públicos human_access/m2m_access; B404/B603 nos dois scripts que executam ferramentas por argv fixo, sem shell/entrada HTTP. Não há supressão. A execução intermediária `gate/` tem 229 testes; `gate-final/` tem 233 e é a referência de fechamento.

O gate CI avalia pytest/SAST/SCA; ZAP é auditoria separada. A aprovação de integração não elimina seu HIGH. O [PR #15](https://github.com/leandro-infnet/medical-appointment-api/pull/15) demonstrou merge bloqueado por teste deliberadamente falho fora da main; limites de scanners têm testes e reprovação SCA local próprios.

| Risco residual | Decisão / condição para reavaliar |
| --- | --- |
| HTTP e ZAP-04 | Aceito só no ensaio fictício em loopback; bloqueia produção. Verificar TLS/certificado, proxy confiável, esquema/IP, cookie Secure e repetir tráfego HTTPS |
| Swagger com CDN e sem CSP/SRI | Aceito só localmente. Remover docs públicas ou servir assets fixados com política compatível; conferir em navegador/scan |
| Auditoria persistente TM-007 ausente | Bloqueia operação clínica real. Registrar ator/ação/alvo mínimo/instante/resultado, acesso/retenção e testes, sem dados clínicos/segredos |
| MFA simulado e cadastro local | Bloqueia uso clínico real. Definir identidade/MFA reais e ciclo de vida/revogação |
| Quotas em memória e volume não medido | Não comprovam defesa de DoS. Definir topologia e verificar carga/coordenação conforme uso |
| Backup/restore e evolução de schema | Bloqueia dados reais sem procedimento. Ensaiar recuperação/migração e permissões |
| OA-03: PATCH aceita null no schema, rejeita em execução | Aceitável com cliente instruído a omitir campos; alinhar antes de distribuir SDK |
| Cobertura passiva limitada | Ampliar verificação no ambiente implantável; ausência de alerta não fecha regras de negócio |
| Ex. 8/9: paciente/histórico/SQL isolados | Aceite acadêmico pendente; manter separados de achados reais da aplicação |

## Entrega

- [ ] PR/check remoto das alterações finais aprovado.
- [ ] Vídeo de até cinco minutos, no YouTube não listado, com link na entrega.
- [ ] ZIP final revisado, sem `.env`, bancos/cadastro real, credenciais, ambiente virtual ou caches.

A pasta Drive do README é apoio; publicação no YouTube não listado continua necessária. Novo ZIP/vídeo não foram produzidos nesta auditoria.

Referências: [ZAP passivo](https://www.zaproxy.org/docs/docker/baseline-scan/), [regra 10105](https://www.zaproxy.org/docs/alerts/10105/), [OWASP 2021](https://owasp.org/Top10/2021/), [BOLA API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/).
