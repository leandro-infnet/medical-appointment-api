# Revisão documental — Exercício 5

## Baseline e escopo

Baseline `e2f239badbaa6905ef32cdfe9423e0fa33b61065`, entrega do Exercício 4; branch observada inicialmente: `feat/ex04-stride-threat-model`. Inspecionados requisitos do exercício/rubrica, documentação permanente, aplicação e catálogo de ameaças/controles. O incremento produz arquitetura de segurança sem mudanças funcionais.

## Resultados da revisão

| Verificação | Resultado / limite |
| --- | --- |
| Partições correspondem ao código | P-01 rotas JSON/schemas, P-02 agenda/templates, P-03 operações e D-01 memória; `main.py` compõe a aplicação |
| Componentes futuros estão separados | Auth, middleware, SQLModel, configuração, TLS/proxy e M2M identificados como planejados; sem interfaces de rede implantadas presumidas |
| Fluxos têm vínculo com o DFD | F-01–10 preservados; visão de partições agrupa pares, DFD mantém direção/dados detalhados |
| Fronteiras reais/lógicas/futuras corretas | TB-01 exterior/processo, TB-02 divulgação lógica; TB-03/04 futuras; armazenamento atual no processo |
| Três eixos cobertos | VD-01–04 design, VI-01–04 implementação, VF-01–04 infraestrutura, total de 12 vetores com TM/CTRL/teste ou inspeção previstos |
| Todos os controles têm responsável lógico | CTRL-01–11 localizados em identidade, política, schemas/apresentação, persistência, middleware/rede e observabilidade |
| Autenticação não substitui ownership | Verificador JWT central; decisão exige recurso/vínculo e restrição de conjuntos; middleware não deduz ownership da URL |
| Nenhuma apresentação fica fora da política planejada | JSON, lista/filtros e agenda precisam de identidade/escopo; permissão ocorre antes de divulgação ou mutação |
| Contratos atuais foram preservados | PATCH não adquire campo de troca de profissional; entradas extras não são descritas como mass assignment comprovado |
| Pendências antes do Ex. 6 estão claras | Vínculo/matriz, JWT/MFA e transporte de identidade HTML; cookie condiciona nova avaliação de CSRF, sem sessão já existente |
| Persistência/operação não recebem garantias falsas | Lock não assegura sobreposição; motor, conflitos, recuperação, processos e TLS a definir; mocks não comprovam transação/concorrência |
| R09 rastreado | Relatório, fonte/exports, DEC-17, requisitos e matriz central localizam entrega e verificação |

## Continuidade e evidências

O threat model foi complementado com seção arquitetural 1.1, conservando os 16 Threat IDs e o snapshot 1.0. Não houve mudança de estado de CTRL ou novo finding. SVG/PNG são renderizações reais de Mermaid 10.9.3; o PNG foi inspecionado visualmente. A conferência técnica da fonte, IDs, links, hashes e código inalterado está em `baseline.txt`.

Não foram executados pytest, scanner, exploração, carga, JWT, M2M ou SQL. As evidências funcionais/segurança do Ex. 2 continuam históricas e delimitadas aos seus cenários. A arquitetura orienta implementação futura; não comprova liberação para dados reais ou produção.
