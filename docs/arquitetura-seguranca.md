# Arquitetura de segurança — Exercício 5

O baseline `e2f239badbaa6905ef32cdfe9423e0fa33b61065` tinha JSON, HTML e memória. O Ex. 5 definiu partições e doze vetores nos eixos design, implementação e infraestrutura (R09). [Diagrama original](../evidencias/ex05/particoes-seguranca.svg), [fonte](particoes-seguranca.mmd) e [revisão](../evidencias/ex05/revisao_documental.md) preservam esse planejamento; o [DFD atual](dfd-atual.mmd) mostra a implementação final.

## Partições implementadas

| Partição | Código / responsabilidade | Controle |
| --- | --- | --- |
| Composição | `app/main.py`: lifespan, routers, handlers e middleware | Ordem dos controles e estado por execução |
| P-01 JSON | `routes/consultas.py`, contratos Pydantic | Entrada, ownership e response_model |
| P-02 HTML | `routes/agenda.py`, `templates/` | Papel da recepção, projeção mínima e escape |
| P-03 operações | `database/consultas.py` | Parâmetros, transação e conflitos |
| P-04/P-05 identidade/política | `auth/`, cadastro confiável no servidor | JWT, bcrypt, MFA, papel/vínculo/recurso |
| P-06 disponibilidade | Rotas/modelos/dados de disponibilidade | Client Credentials e scopes mínimos |
| D-01 SQLite | `models/tabelas.py`, `database/session.py` | PK/FK/CHECK, sessão por requisição |
| Rede/configuração | `network.py`, `settings.py` | CORS, headers, cotas e segredos externos |

As partições são responsabilidades no mesmo processo, não microserviços ou isolamento de segurança. A autenticação é central; autorização por objeto usa recurso/vínculo e ocorre antes da divulgação ou mutação.

## Fluxos e fronteiras

- JSON: E-01 → P-01 → P-03 → D-01, F-01–04/09–10. Entrada validada, identidade/política, operação e saída filtrada.
- HTML: E-02 → P-02 → P-03 → D-01, F-05–10. Restrição à recepção antes da projeção e renderização.
- M2M: autenticação/consulta do parceiro em F-26–33, sem transferência de paciente ou motivo.
- TB-01: exterior/processo; TB-02: contrato público versus entidade interna; TB-03: parceiro/API; TB-04: acesso ao arquivo SQLite. A separação em pastas não isola memória ou permissões do SO.
- Transporte HTTPS/proxy de produção ainda requer definição e teste; localhost não fornece essa garantia.

## Vetores identificados no baseline

Design cobre contrato e permissão; implementação cobre cumprimento em código; infraestrutura cobre rede, configuração e operação. A tabela mantém o planejamento do Ex. 5; o fechamento atual está no [threat model](threat-model.md).

| Vetor / eixo | Cenário relevante e estado | Componente / fluxo / fronteira | Threat ID | Decisão / controle / verificação |
| --- | --- | --- | --- | --- |
| VD-01 — design | Papel ou ID isolado permite gerir paciente fora do vínculo; política ausente | P-01/P-03, F-01/03/09, TB-01 | TM-001/003/006 | CTRL-01/02: identidade + papel/atributo + recurso; TEST-04/07/08/17 futuros; matriz de vínculo a definir |
| VD-02 — design | Permissão unitária não cobre lista/agenda; vazamento por filtro/dia | P-01/P-02, F-02/06, TB-01/02 | TM-002/004 | CTRL-02/03/04: escopo do conjunto + mínima saída; TEST-09 futuro, TEST-02 histórico cobre somente campos |
| VD-03 — design | Regra de estado/duração/conflito indefinida permite agenda incoerente | P-03/D-01, F-09/10 | TM-006/009 | Decidir regra antes de disponibilidade; CTRL-05/08; TEST-12/16 após decisão, sem conflito alegadamente demonstrado |
| VD-04 — design | Token de parceiro confundido com humano ou admin ganha leitura clínica por nome do papel | Identidade/cliente futuros; TB-03 | TM-013/014 | CTRL-01/02/10; RBAC + vínculo como direção proposta, escopos M2M separados; TEST-06/10/11 futuros |
| VI-01 — implementação | Entrada parcialmente validada; status livre, extras não proibidos, IDs sem vínculo | Schemas/P-01/P-03, F-01/03 | TM-003/006 | CTRL-05/02: `extra='forbid'`, allowlists/regex pertinentes e semântica; TEST-12 parcial histórico/futuro; não presumir mass assignment |
| VI-02 — implementação | Retornar objeto inteiro ou desativar escape reintroduz exposição/XSS | P-01/P-02, F-04/08/02/06, TB-02 | TM-004/005 | CTRL-03/04 existentes; preservar TEST-02/03 históricos; nenhuma regressão vulnerável criada |
| VI-03 — implementação | Verificador JWT esquece expiração/claims, ou rota contorna política central | Auth/middleware futuros; F-01/05 | TM-001/002/003/013 | CTRL-01/02: validação única do token e decisão de recurso obrigatória; TEST-05/07/09/17 futuros |
| VI-04 — implementação | Erros refletem clínica e ações não deixam registro atribuível | P-01/P-02/P-03, F-02/06/09 | TM-007/011 | CTRL-06/09; política de auditoria/erro a definir; TEST-19/22 propostos, sem execução |
| VF-01 — infraestrutura | HTTP exposto permite observação/alteração de dados em trânsito | TB-01, F-01/02/05/06; topologia futura | TM-012 | CTRL-11: decidir TLS/proxy/origens; TEST-15 e inspeção de HTTPS futura; comando local HTTP não comprova ataque externo |
| VF-02 — infraestrutura | Memória volátil por worker e lock local dão perda/divergência após reinício | P-03/D-01, F-09/10 | TM-008/010 | CTRL-08/07: banco e limites coerentes com workers; TEST-20/21 futuros; sem teste concorrente/capacidade |
| VF-03 — infraestrutura | Segredo previsível ou credencial de banco exposta compromete futuros tokens/dados | Configuração/auth/banco futuros, TB-01/04 | TM-013/015 | CTRL-01/08: BaseSettings/.env sem credencial real no repositório/ZIP; inspeção de configuração futura e TEST-05/13; não há segredo real hardcoded encontrado |
| VF-04 — infraestrutura | Falta de limites, headers e revisão de exposição amplia abuso/exploração | Processo HTTP, SUP-05/06 e login futuro | TM-005/008/012/016 | CTRL-07/11: rate limiting login, CORS explícito e headers; TEST-14/15 futuros; exposição de `/docs` a definir |

## Decisões e alternativas

RBAC com vínculo/ownership evita permissão clínica entre profissionais; motor ABAC genérico e microserviços acrescentariam complexidade sem necessidade. JSON/HTML usam o mesmo validador e políticas, enquanto middleware trata identidade e a política decide o recurso. SQLModel mantém sessão/transação no acesso a dados; lock em memória não oferecia durabilidade nem exclusão entre processos.

As decisões de matriz, cookie, M2M, duração/fuso/status e SQLite estão em DEC-17–23 de [decisões](decisoes.md). Auditoria persistente, TLS e recuperação continuam no [capstone](relatorio-capstone.md). Testes finais exercitam os fluxos; as imagens Ex. 5 são evidência de design, não de execução autenticada naquele baseline.
