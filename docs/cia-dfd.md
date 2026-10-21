# CIA, referenciais e DFD — Exercício 3

Baseline histórico: `46db788b99a19b4cf145555e8e9ff679a88e29fe` (Ex. 2). Havia CRUD, response models, agenda com escape e memória; sem identidade, M2M ou banco. As tabelas abaixo registram os riscos e controles daquele momento. R05: CIA/referenciais; R06: DFD e fronteiras.

## Ativos

| ID | Ativo / campos reais | Entrada / armazenamento / saída | Sensibilidade e cuidado |
| --- | --- | --- | --- |
| AT-01 | Vínculo: `id`, `paciente_id`, `profissional_id`, `data_hora`, `status` | JSON de entrada; D-01; JSON de saída; agenda com horário e IDs | Identifica agendamentos e associa pessoas a atendimento; não é dado público por usar números |
| AT-02 | Informação clínica: `motivo` | POST/PATCH; D-01; JSON; excluído do contexto HTML | Informação de saúde; precisa de autorização além do schema |
| AT-03 | Nota interna: `observacoes_internas` | POST/PATCH; D-01; ausente do JSON/HTML de sucesso | Pode conter informação clínica confidencial; excluir da saída não impede escrita indevida |
| AT-04 | Metadados: `criado_em`, `atualizado_em` e contador | Gerados internamente; D-01; datas excluídas das respostas | Datas não são trilha de auditoria: falta ator, ação e histórico; contador torna IDs previsíveis |
| AT-05 | Serviço, código e templates | Processo FastAPI, módulos e templates locais | Alteração indevida pode remover controles; queda ou reinício afeta agenda e dados |
| AT-06 | Evidências e testes fictícios | `tests/`, `evidencias/`, fora do fluxo de produção | Não usar dados reais; payload didático não é finding de ataque executado em produção |


## Análise CIA

Confidencialidade limita divulgação; integridade protege estados/alterações; disponibilidade inclui uso e recuperação da agenda.

| ID | Ativo / propriedade | Cenário de falha e consequência | Controle atual | Verificação e lacuna |
| --- | --- | --- | --- | --- |
| CIA-01 | AT-03/04 — C | Retornar entidade interna completa revela notas e auditoria ao consumidor | `ConsultaResponse` exclui três campos em POST/GET/lista/PATCH | TEST-02 e JSON Ex. 2; cobre saída de sucesso, não autorização nem todos os erros |
| CIA-02 | AT-01/02 — C | Cliente sem identidade lê consulta por ID/listagem ou agenda e conhece atendimento | Minimização da agenda reduz os campos; **nenhum controle de acesso atual** | Inspeção das rotas confirma ausência de dependência de identidade; autorização prevista Ex. 6, M2M Ex. 7 |
| CIA-03 | AT-01/05 — C/I | Texto malicioso armazenado em status vira marcação ativa na agenda, podendo afetar sessão/página da recepção | Auto-escape Jinja2, sem `safe`, e contexto mínimo | TEST-03 com script e imagem/handler; protege contexto HTML usado, não qualquer contexto JavaScript/CSS |
| CIA-04 | AT-01/02 — I | Entrada ausente/incompatível ou PATCH com nulo invalida campos obrigatórios | Pydantic, `gt`, limites de motivo/notas e validator de nulos | Teste de PATCH nulo e data inválida; validação semântica de vínculo, catálogo de status e `extra='forbid'` ainda ausentes |
| CIA-05 | AT-01/03 — I | Cliente altera/deleta consulta alheia ou escreve notas internas indevidamente | **Nenhuma autenticação ou autorização atual** | Rotas e schemas permitem acesso sem identidade; Ex. 6 precisa validar recurso e vínculo, não apenas papel |
| CIA-06 | AT-01/04 — I | Acesso concorrente ao dicionário/contador causa atualização inconsistente | `_lock` envolve operações em memória | Inspeção do código; não foi realizado teste concorrente e não há garantia de conflito de intervalos nem coordenação entre processos |
| CIA-07 | AT-01/05 — A | Reinício elimina consultas; workers independentes veem estados diferentes | Memória simplifica demonstração, **sem durabilidade/recuperação** | Característica estrutural de D-01; Ex. 11 precisa decidir banco/recuperação, sem prometer backup já existente |
| CIA-08 | AT-05 — A | Muitas escritas/listagens sem paginação consomem memória e CPU; lock pode serializar operações | Alguns limites de campos evitam parte das entradas excessivas | Não há quota, rate limiting ou limite de registros; capacidade não medida; hardening Ex. 10 e limites a definir |


## DFD e fluxos sensíveis

[SVG histórico](../evidencias/ex03/dfd-atual.svg), [PNG](../evidencias/ex03/dfd-atual.png) e [fonte atual](dfd-atual.mmd). O diagrama atual incorpora identidade, M2M e SQLite; as exportações antigas preservam o baseline. P-01 representa HTTP JSON, P-02 HTML/Jinja2 e P-03 acesso a dados, todos no mesmo processo.

| Fluxo | Origem → destino | Dados e forma | Fronteira / proteção atual |
| --- | --- | --- | --- |
| F-01 | E-01 → P-01 | HTTP: JSON com IDs, data/hora, motivo, notas; URL com ID/filtros | TB-01; validação parcial de entrada; sem TLS no comando local, autenticação ou ownership |
| F-02 | P-01 → E-01 | HTTP: seis campos JSON, erros ou 204 sem corpo | TB-01 e limite lógico TB-02; `ConsultaResponse` filtra sucesso; não aplicar a mesma afirmação aos erros |
| F-03 | P-01 → P-03 | Chamada Python: modelo de entrada ou ID/filtros/operação | Sem travessia de isolamento; dados tipados continuam controlados pelo solicitante |
| F-04 | P-03 → P-01 | Consulta completa, lista, `None` ou resultado de remoção | TB-02 lógico: P-01 deve filtrar dados internos antes de F-02 |
| F-05 | E-02 → P-02 | HTTP GET: `dia` opcional; nunca identidade da recepção comprovada | TB-01; parsing de date; default do dia no fuso local |
| F-06 | P-02 → E-02 | HTTP HTML: IDs, horário, status e dia; texto escapado | TB-01/TB-02 lógico; sem motivo/notas; navegador interpreta HTML, exigindo escape de texto variável |
| F-07 | P-02 → P-03 | Chamada Python com dia local para leitura | Sem isolamento; filtro de dia não é filtro de autorização |
| F-08 | P-03 → P-02 | Lista de entidades completas do dia, em ordem local | TB-02 lógico: projeção em P-02 elimina campos antes de entregar contexto ao Jinja2 |
| F-09 | P-03 → D-01 | Acesso Python: busca, inserção, alteração/remoção e contador | Mesmo espaço de memória; operações sob lock; sem SQL/credenciais |
| F-10 | D-01 → P-03 | Registros completos com notas, motivo, auditoria e IDs | Mesmo processo; instanciados como `Consulta`; lock não limita quem está autorizado |


TB-01 separa cliente/processo. TB-02 é redução lógica de divulgação, sem isolamento entre módulos. TB-03, introduzida no Ex. 7, separa laboratório/API. TB-04 representa acesso ao arquivo SQLite pelas permissões do SO, sem rede de banco.

No JSON, notas entram por F-01 e passam por P-03/D-01, mas são excluídas de F-02. No HTML, P-02 reduz os registros recebidos por F-08 antes de renderizar F-06. Saídas de erro também exigem revisão: response_model de sucesso não as filtra.

## Referenciais aplicados

Edições adotadas: OWASP Top 10:2021, API Security Top 10:2023, SSDF 1.1/SP 800-218 e MITRE CWE 4.20. CWE descreve fraquezas; SSDF organiza práticas de desenvolvimento. O mapeamento é parcial, sem alegação de certificação.

| Referencial / item | Controle existente e justificativa | Código / evidência | Limitação |
| --- | --- | --- | --- |
| [OWASP API3:2023 — propriedades do objeto](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) | Allowlist da resposta e projeção HTML reduzem exposição de propriedades internas | `ConsultaResponse`, rota agenda; TEST-02 e comparação JSON Ex. 2 | Redução de exposição não implementa autorização de leitura/escrita por propriedade |
| [OWASP A03:2021 — Injection](https://top10.owasp.org/2021/A03_2021-Injection/) | Auto-escape evita interpretar texto armazenado como HTML ativo; validação limita parte das entradas | Environment da agenda e templates; TEST-03 com dois payloads | XSS integra A03 nesta edição; não existe SQL atual e não foi comprovada defesa de SQL injection |
| [NIST SSDF 1.1 — PW.5.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) | Validação, filtragem e encoding são práticas de codificação segura aplicadas às fronteiras | Schemas, rotas e templates Ex. 1/2 | Parcial: falta autorização e validação estrita |
| NIST SSDF 1.1 — PW.8.2, mesma publicação | Testes de contratos e XSS com resultados preservados | `tests/test_respostas_templates.py`, `evidencias/ex02/pytest_output.txt` | Não cobre todas as ameaças; expansão derivada do STRIDE no Ex. 12 |
| NIST SSDF 1.1 — PW.1.2, mesma publicação | Requisitos, decisões e riscos mantidos em documentos versionáveis | `docs/requisitos.md`, `docs/decisoes.md`, `docs/rastreabilidade.md` e este relatório | Registro existente não demonstra implantação integral do SSDF |
| [MITRE CWE-79 — XSS](https://cwe.mitre.org/data/definitions/79.html) | Escape de saída evita ativação dos payloads HTML testados | P-02; TEST-03, HTML e screenshot Ex. 2 | Defesa dos contextos usados; nenhum bypass demonstrado no estado atual |
| [MITRE CWE-200 — exposição sensível](https://cwe.mitre.org/data/definitions/200.html) | Filtragem de campos e minimização reduzem divulgação interna | P-01/P-02; TEST-02 e contexto verificado | Exposição de dados clínicos sem controle de acesso permanece; categoria ampla não substitui causa específica |
| [MITRE CWE-20 — validação inadequada](https://cwe.mitre.org/data/definitions/20.html) | Campos tipados, limites e bloqueio de nulos reduzem estados inválidos | Schemas, teste PATCH nulo e agenda com data inválida | Não comprova integridade referencial, ownership ou whitelist de status |


## Evolução das lacunas

| Lacuna histórica | Controle posterior / limite |
| --- | --- |
| LAC-01: sem identidade/ownership | Ex. 6: papel, vínculo e recurso; middleware Ex. 9 |
| LAC-02: extras/status livres | Ex. 9: extra forbid, allowlist e regex |
| LAC-03: abuso/listagens sem limite | Ex. 10: cotas 5/60; paginação/capacidade não demonstradas |
| LAC-04: memória e conflito | Ex. 11: SQLModel/SQLite, transações e sobreposição; recuperação operacional pendente |
| LAC-05: M2M/rede | Ex. 7/10: scopes, CORS e headers; TLS real pendente |
| LAC-06: erros/auditoria | Handler 422 mínimo; auditoria persistente permanece aberta |

Resultados, revisão e renderização: [Ex. 3](../evidencias/ex03/README.md). Continuidade: [STRIDE](threat-model.md), [rastreabilidade](rastreabilidade.md) e [riscos finais](relatorio-capstone.md).
