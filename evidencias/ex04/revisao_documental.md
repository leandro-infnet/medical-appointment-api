# Revisão documental — Exercício 4

## Baseline e método

Aplicação em `fe31673e1ed4e0238277abe0b111d66be1363c9e`, integração do Exercício 3; branch observada: `main`. Foram inspecionados os requisitos acadêmicos, a rubrica, a documentação técnica, CIA/DFD, rotas, schemas, armazenamento e testes/evidências existentes. A revisão produziu threat model 1.0 sem mudanças funcionais.

## Conferências realizadas

| Critério | Resultado |
| --- | --- |
| R07: misuse cases da própria aplicação | 12 cenários MU-001–012 possuem ator, precondição, tentativa, resultado proibido e vínculo com ameaça, fluxo/superfície e controle/teste |
| R08: pelo menos três componentes | P-01 (JSON), P-02 (agenda HTML), P-03 (acesso a consultas) correspondem ao DFD/código |
| Seis categorias em cada componente | S/T/R/I/D/E examinadas nas 18 linhas, com propagação e cenários futuros explicitados |
| Ativos e fluxos preservados | AT-01–06, F-01–10 e TB-01/02 não foram renumerados; TB-03/04 continuam futuras |
| Superfícies efetivas | HTTP/corpos/IDs/filtros/HTML/memória/erros descritos; P-03 sem endpoint independente; login/M2M/SQL separados como futuros |
| Ameaças e controles rastreáveis | TM-001–016 possuem CTRL e testes na matriz; CTRL-03/04 verificados historicamente, demais controles têm estado parcial/planejado |
| Ownership e BOLA não são reduzidos a autenticação | MU-002/003, TM-002/003 e TEST-07/09 cobrem leitura, lista, HTML e mutação; caso de paciente autenticado do Ex. 8 permanece pendente |
| Contrato PATCH respeitado | Schema atual não permite editar `profissional_id`; o modelo não inventa essa operação e distingue campo extra ignorado de mass assignment comprovado |
| Limites de proteção da memória | Lock não garante exclusividade de intervalo/durabilidade; reinício é incidente operacional, não poder remoto de qualquer cliente |
| Priorização não fabrica métricas | Prioridade qualitativa justificada pelo dado/impacto; CVSS e gate para Ex. 12; TM-009 depende da regra de agenda |
| Ausência de novas provas de exploração | Ataques/carga/concorrência não executados; hipótese de erro sensível identificada como hipótese; XSS atual mitigado não foi reintroduzido |
| Risco residual associado ao controle | Seção 7 registra lacunas de cada CTRL; fechar ameaça exige resultado efetivo e revisão, não apenas intenção |

## Referências e evolução

Foi consultada a documentação oficial Microsoft STRIDE e a OWASP Threat Modeling Cheat Sheet, citadas no relatório. As edições dos referenciais de classificação permanecem DEC-15; STRIDE é técnica de identificação, não severidade/CVSS nem categoria OWASP.

TEST-01–18 mantêm o catálogo de cenários funcionais e de segurança descrito na seção 8 do threat model. TEST-19–22 são cenários adicionais propostos para auditoria, limites de volume, durabilidade e tratamento de erros, identificados como recomendações de engenharia. O snapshot inicial permite conferir posteriormente o que foi mitigado e quais riscos permaneceram.

## Resultado da etapa

Threat model e evidências documentais produzidos para R07/R08. Conferência de referências/IDs e ausência de mudanças na aplicação registradas em `baseline.txt`. Nenhum resultado de segurança futuro é apresentado como teste executado; não houve autorização de deploy.
