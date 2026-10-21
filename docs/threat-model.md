# Threat model STRIDE — Exercícios 4 a 13

O modelo começou no baseline `fe31673e1ed4e0238277abe0b111d66be1363c9e`, com JSON, HTML e memória. O [snapshot inicial](../evidencias/ex04/threat-model-v1.md) preserva o planejamento; este documento consolida o estado final, mantendo os IDs. Modelagem não equivale a exploração executada.

Método: CIA → DFD/fronteiras → ativos → superfícies → misuse cases → STRIDE → controles → testes. Fontes: [Microsoft STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats), [OWASP Threat Modeling](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html), [CIA](cia-dfd.md) e [DFD](dfd-atual.mmd).

## Ativos, componentes e superfícies

| ID | Ativo | Proteção |
| --- | --- | --- |
| AT-01 | IDs/vínculos, horário e status da consulta | C/I/A |
| AT-02 | Motivo clínico | C/I |
| AT-03 | Notas internas | C/I |
| AT-04 | Timestamps e identificadores internos | I; não são trilha de auditoria |
| AT-05 | Serviço, código e templates | I/A |
| AT-06 | Testes e evidências fictícias | I |
| AT-07 | Credenciais, hashes, chave, desafios e tokens | C/I |

P-01: API JSON; P-02: agenda HTML; P-03: operações/dados; P-04/P-05: identidade/política; P-06: disponibilidade. Todos compartilham o processo FastAPI. TB-01 é exterior/API; TB-02 é divulgação lógica; TB-03 é parceiro/API; TB-04 é acesso ao arquivo SQLite pelo SO.

| ID | Superfície / dados | Fluxos ou fronteiras |
| --- | --- | --- |
| SUP-01 | POST/PATCH consultas; IDs, data, motivo, notas, status | F-01/03/09; TB-01 |
| SUP-02 | Leitura/lista/alteração/remoção por ID e filtros | F-01–04; TB-01/02 |
| SUP-03 | Agenda diária e HTML | F-05–08; TB-01/02 |
| SUP-04 | Sessão SQLModel, entidades e SQLite | F-09/10; TB-04 |
| SUP-05 | Erros e transporte | F-02/06; TB-01 |
| SUP-06 | Raiz, Swagger, ReDoc e OpenAPI | Metadata pública |
| SUP-07 | Login, JWT, MFA e administração | F-11–25; TB-01 |
| SUP-08 | Token/consulta M2M | F-26–33; TB-03 |
| SUP-09 | Persistência relacional e configuração | TB-04 |
| SUP-10 | Cookie da agenda | F-05/16/24/25; TB-01 |

## Misuse cases

São cenários de análise; as colunas de controle/teste apontam sua verificação, não afirmam sucesso de ataque.

| ID / ator e precondição | Tentativa / resultado proibido | Relação / controle / teste |
| --- | --- | --- |
| MU-001: cliente sem identidade, criação exposta | Declarar profissional/paciente alheio e atribuir atendimento | TM-001/003; F-01/03/09; CTRL-01/02; TEST-04/08 |
| MU-002: usuário sem direito ao recurso | Trocar ID/filtro/dia e conhecer consulta/agenda alheia | TM-002; F-01/02/05/06; CTRL-02; TEST-07/09 |
| MU-003: usuário sem direito de gestão | PATCH/DELETE alheio alterando/removendo atendimento | TM-003; F-01/03/09; CTRL-02; TEST-07/17 |
| MU-004: entrada com tipagem básica válida | Criar vínculo inválido ou estado/conflito incoerente | TM-006/009; F-01/09; CTRL-05/08; TEST-08/12/16 |
| MU-005: HTML malicioso persistido | Status com script executar na agenda | TM-005; F-01/09/08/06; CTRL-04; TEST-03 |
| MU-006: autor nega uma ação | Alteração/leitura sem registro atribuível | TM-007; F-01/05/09; CTRL-06; TEST-19 pendente |
| MU-007: cliente automatizado | Volume de escrita/listagem impedir atendimento | TM-008; F-01/02/05/06/09; CTRL-07; TEST-14/20 |
| MU-008: incidente de processo | Reinício/workers perderem ou divergirem da agenda | TM-010; D-01/F-09/10; CTRL-08; TEST-21 |
| MU-009: entrada inválida sensível | Erro/log repetir dado clínico ou segredo | TM-011; F-01/02; CTRL-09; TEST-22 |
| MU-010: conta comum/token adulterado | Acessar admin ou pular MFA | TM-013; SUP-07; CTRL-01/02; TEST-05/06/10 |
| MU-011: parceiro com token legítimo | Obter privilégio humano ou dados clínicos | TM-014; TB-03; CTRL-10; TEST-11 |
| MU-012: cliente com payload SQL | Transformar valor em estrutura SQL e ampliar leitura | TM-015; F-09/10; CTRL-08; TEST-13 |
| MU-013: cookie roubado ou indução cross-site | Ler agenda indevidamente ou autenticar mutação por cookie | TM-017; SUP-10; CTRL-12; TEST-23 |

O cenário de paciente autenticado do Ex. 8 foi demonstrado separadamente em DEMO-001. A aplicação não possui portal/prontuário de paciente; o aceite desse recorte permanece pendente. Payloads históricos de XSS já eram escapados.

## STRIDE em três componentes

S: identidade falsa; T: alteração; R: repúdio; I: divulgação; D: indisponibilidade; E: elevação de privilégio. As 18 avaliações localizam riscos propagados entre módulos, sem presumir uma rede entre eles.

| Componente | Categoria | Cenário / Threat ID | Controle atual ou lacuna |
| --- | --- | --- | --- |
| P-01 JSON | S | ID declarado confundido com autor; TM-001/013 | Identidade JWT e cadastro confiável |
| P-01 | T | PATCH/DELETE ou vínculo alheio; TM-003/006 | Política por recurso e schemas |
| P-01 | R | Ação sem autoria persistida; TM-007 | Auditoria pendente |
| P-01 | I | Objeto/lista/erro expor dados; TM-002/004/011 | Ownership, response models e handler mínimo |
| P-01 | D | Criações/listagens amplas; TM-008 | Cota local; paginação/capacidade pendentes |
| P-01 | E | Poder clínico/admin indevido; TM-003/013 | Papel, vínculo, ownership e MFA |
| P-02 HTML | S | Navegador alegar recepção; TM-001 | Mesmo validador JWT; papel obrigatório |
| P-02 | T | Status alterar semântica da página; TM-005 | Auto-escape e CSP |
| P-02 | R | Leitura não atribuível; TM-007 | Auditoria pendente |
| P-02 | I | Agenda/conteúdo além da permissão; TM-002/004 | Recepção mínima, projeção e no-store |
| P-02 | D | Leitura diária onerosa; TM-008 | Cota local; volume não medido |
| P-02 | E | Cookie conceder acesso clínico; TM-017 | Cookie só em GET da agenda |
| P-03 dados | S | Operação sem principal confiável; TM-001 | Política aplicada antes da operação |
| P-03 | T | Escrita indevida/conflito; TM-003/006/009 | Ownership, FK/CHECK e transação |
| P-03 | R | Sem histórico/ator; TM-007 | Timestamps insuficientes |
| P-03 | I | Entidade interna chegar inteira ao cliente; TM-004 | Redução em P-01/P-02 |
| P-03 | D | Perda/lock/concorrência; TM-008/010 | SQLite e 503; recuperação operacional pendente |
| P-03 | E | Escrita privilegiada sem política; TM-003 | Autorização antes da gravação; sem endpoint independente |

## Catálogo de ameaças e fechamento

P1/P2 são prioridades qualitativas do modelo; CVSS e impacto dos findings estão em [DevSecOps](devsecops.md). Mitigação local não fecha automaticamente risco de implantação.

| ID | Ativos / superfície / STRIDE | Risco e prioridade | Controle, teste e residual |
| --- | --- | --- | --- |
| TM-001 | AT-01/04/07; SUP-01/03/07; S | Agir sem identidade; P1 | CTRL-01/02, TEST-04/08; TLS real pendente |
| TM-002 | AT-01/02; SUP-02/03; I/E | Leitura cruzada; P1 | CTRL-02, TEST-07/09; BOLA de paciente apenas didática |
| TM-003 | AT-01–03; SUP-01/02/04; T/E | Mutação alheia; P1 | CTRL-02, TEST-07/08/17; estado intacto após negação |
| TM-004 | AT-02–04; SUP-02/03/04; I | Exposição de entidade interna; P2 | CTRL-03/04, TEST-02/09; campos novos exigem revisão |
| TM-005 | AT-01/05; SUP-01/03; T/I/E | XSS persistido; P2 | CTRL-04/05, TEST-03; CSP agenda, sem teste de browser real |
| TM-006 | AT-01/02; SUP-01/04; T | Vínculo/estado inválido; P1/P2 | CTRL-02/05/08, TEST-08/12/16; regras explícitas |
| TM-007 | AT-01/03/04; SUP-01–04; R | Ação sem atribuição; P2 | CTRL-06/TEST-19 pendentes; bloqueia operação clínica real |
| TM-008 | AT-05; SUP-01–04; D | Exaustão de recursos; P1 | CTRL-07, TEST-14; TEST-20/capacidade pendentes |
| TM-009 | AT-01; SUP-04; T | Sobreposição de intervalos; P1 | CTRL-08, TEST-16; proteção depende de escrita pela API |
| TM-010 | AT-01/05; SUP-04; D/T | Perda/divergência após reinício; P1 | CTRL-08, TEST-21; durabilidade verificada, restore não ensaiado |
| TM-011 | AT-02/03; SUP-05; I | Erro/log com conteúdo sensível; P2 | CTRL-09, TEST-22; handler 422 mínimo; revisar mensagens futuras |
| TM-012 | AT-01–03/07; SUP-05/06; S/T/I | Tráfego interceptável; P1 | CTRL-11/TEST-15 parcial; ZAP-04, TLS real bloqueia deploy |
| TM-013 | AT-07; SUP-07; S/E | JWT/claims/papel/MFA indevidos; P1 | CTRL-01/02, TEST-05/06/10; MFA simulado e revogação limitada |
| TM-014 | AT-01/02/07; SUP-08/TB-03; S/I/E | M2M virar humano; P1 | CTRL-10, TEST-11; bearer roubado lê disponibilidade até expirar |
| TM-015 | AT-01–03; SUP-09/TB-04; T/I | SQL Injection; P1 | CTRL-08, TEST-13 com SQLite real; ANTES SQL isolado no Ex. 9 |
| TM-016 | AT-05/07; SUP-07; S/D | Adivinhação/abuso de login; P1 | CTRL-01/07, TEST-04/14; NAT/workers/IPs distribuídos residuais |
| TM-017 | AT-01/07; SUP-10; S/T/E | Sessão/cookie indevido; P1 | CTRL-12, TEST-23; logout não revoga cópia do JWT |

## Controles e localização

| ID | Implementação / estado |
| --- | --- |
| CTRL-01 | `auth/passwords.py`, `tokens.py`, `mfa.py`, `middleware.py`: bcrypt, JWT expirável, claims e MFA simulado |
| CTRL-02 | `auth/policies.py`: papel, vínculo e ownership para recurso, criação e listagem |
| CTRL-03 | `ConsultaResponse` em `models/consultas.py` e rotas JSON |
| CTRL-04 | `routes/agenda.py`, templates: projeção mínima, herança e auto-escape |
| CTRL-05 | Schemas: extra forbid, allowlists/regex e limites |
| CTRL-06 | Auditoria ator/ação/alvo/instante/resultado: pendente; acesso/retenção também a definir |
| CTRL-07 | `network.py`: cota mais restrita em login/M2M/MFA; memória por processo |
| CTRL-08 | `database/`, `models/tabelas.py`: SQLModel, parâmetros, sessão, constraints e transação |
| CTRL-09 | `errors.py`: 422 sem input/contexto/corpo; erro de banco sem detalhe interno |
| CTRL-10 | `auth/m2m.py`, tokens e disponibilidade: cliente, audiência/finalidade/scope |
| CTRL-11 | `network.py`, settings: CORS, headers e CSP agenda; TLS real pendente |
| CTRL-12 | Cookie HttpOnly/Secure/SameSite Strict/path agenda; bearer para mutações |

## Catálogo de testes

| ID | Cenário / arquivo | Estado / evidência |
| --- | --- | --- |
| TEST-01 | CRUD, `test_consultas.py` | Ex. 1 e gate final |
| TEST-02 | Campos internos ausentes, `test_respostas_templates.py` | Ex. 2 e gate final |
| TEST-03 | HTML legado escapado, mesmo arquivo | Ex. 2/9; projeção mockada após CHECK |
| TEST-04 | Credenciais/ausência de token, `test_autorizacao.py` | Ex. 6 e regressão |
| TEST-05 | Assinatura/algoritmo/datas/claims, autorização e M2M | Ex. 6/7 e regressão |
| TEST-06 | MFA pendente/inválido/válido, autorização | Ex. 6 e regressão |
| TEST-07 | GET/PATCH/DELETE cruzados, autorização/STRIDE | Ex. 6/9/12 e gate final |
| TEST-08 | Identidade/vínculo na criação, autorização/entrada | Ex. 6/9 e gate final |
| TEST-09 | Lista/filtros/agenda, autorização/templates | Ex. 6 e regressão |
| TEST-10 | Não admin em rota administrativa, autorização | Ex. 6 e expansão Ex. 12 |
| TEST-11 | M2M permitido/negado, `test_m2m.py` | Ex. 7 e regressão |
| TEST-12 | Extras/nulos/status/limites, entrada/saída | Ex. 9 e gate final |
| TEST-13 | SQL parametrizado, `test_persistencia.py` | Ex. 11; Ex. 9 só didático |
| TEST-14 | Cotas/recuperação, `test_hardening.py` | Ex. 10 e regressão |
| TEST-15 | CORS/headers, hardening; TLS real | HTTP verificado; TLS pendente |
| TEST-16 | Conflito/concorrência/rollback, persistência | Ex. 11, SQLite real |
| TEST-17 | Unidades com mocks, `test_capstone.py` | Ex. 13, sucesso e negação sem escrita |
| TEST-18 | OpenAPI versus HTTP, capstone | Ex. 13 e snapshots |
| TEST-19 | Auditoria mínima sem segredo | Pendente |
| TEST-20 | Limites de volume/listagem e medição | Pendente |
| TEST-21 | Reinício/recuperação, persistência | Reinício em dois processos; restore operacional pendente |
| TEST-22 | Erros sem dados sensíveis, entrada/STRIDE | Ex. 9/12 e regressão |
| TEST-23 | Cookie restrito/inválido/flags, autorização | Ex. 6 e regressão; browser/TLS pendentes |

Evidências por etapa: [Ex. 4](../evidencias/ex04/README.md), [Ex. 12](../evidencias/ex12/README.md), [Ex. 13](../evidencias/ex13/README.md). Gate final: 233 testes aprovados; ZAP: 25 requisições por scan, 15→14 instâncias de alertas. Findings, correções e decisão de bloqueio de produção estão no [capstone](relatorio-capstone.md). IAST permanece proposta; os testes com mocks não comprovam banco, TLS ou navegação real.
