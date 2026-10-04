# Exercício 4 — Misuse cases e threat model STRIDE

## 1. Escopo, baseline e método

**Escopo do Exercício 4:** misuse cases relevantes, STRIDE em pelo menos três componentes e threat model consolidado com ativos, superfícies e mitigações. Este relatório atende **R07 e R08**.

**Versão inicial do modelo:** 1.0. **Baseline da aplicação:** `fe31673e1ed4e0238277abe0b111d66be1363c9e`, integração do Exercício 3, analisado na branch `main`. A aplicação continua com CRUD JSON, agenda HTML e armazenamento em memória.

Contexto reutilizado: [CIA e DFD](cia-dfd.md), [fonte do DFD](dfd-atual.mmd), [diagrama exportado](../evidencias/ex03/dfd-atual.svg) e decisões DEC-13–15. Não há novo fluxo ou componente executável nesta etapa; o DFD permanece válido.

A sequência aplicada é **CIA → DFD → fronteiras → ativos → superfícies → misuse cases → STRIDE → mitigações → testes**. A [Microsoft descreve as seis categorias STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats); a [OWASP recomenda revisar o modelo conforme o sistema evolui](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html). As ameaças abaixo são análise própria da aplicação, não uma lista de findings extraída dessas referências.

| Categoria | Pergunta aplicada |
| --- | --- |
| S — Spoofing | Uma alegação de identidade pode ser aceita sem comprovação? |
| T — Tampering | Consulta, vínculo ou conteúdo pode ser alterado indevidamente? |
| R — Repudiation | Uma ação pode ficar sem atribuição suficiente para investigação? |
| I — Information Disclosure | Dados sensíveis podem chegar a receptor sem autorização? |
| D — Denial of Service | Volume, falha ou perda de estado pode impedir atendimento? |
| E — Elevation of Privilege | Um consumidor pode executar operação além da permissão prevista? |

### Convenções de estado e evidência

- **Lacuna observada no código:** ausência de um controle ou comportamento estrutural identificável por inspeção; não equivale a ataque executado.
- **Mitigação verificada no Ex. 2:** comportamento delimitado demonstrado por testes/evidências históricos; não fecha toda a ameaça.
- **Hipótese a verificar:** cenário plausível cujo resultado não foi demonstrado.
- **Futura/condicional:** depende de recurso, decisão ou topologia ainda inexistente.

`MU` identifica misuse case; `TM` ameaça; `SUP` superfície; `CTRL` controle; `TEST` cenário do catálogo da seção 8 deste documento. AT/P/F/TB preservam os IDs do Ex. 3. LAC-01–06 continuam sendo lacunas, sem renomeá-las como findings. Uma ameaça pode ter várias categorias; a ocorrência em três componentes não exige três IDs diferentes para o mesmo cenário.

## 2. Ativos, atores, componentes e fronteiras

| Ativo preservado | Conteúdo / objetivo de proteção | CIA relevante |
| --- | --- | --- |
| AT-01 | Consulta e vínculo paciente/profissional; horário e status | C/I/A |
| AT-02 | Motivo clínico | C/I |
| AT-03 | Observações internas | C/I |
| AT-04 | Datas de registro/alteração e contador | I; datas não formam trilha de auditoria |
| AT-05 | Serviço, código, templates e capacidade de atender | I/A |
| AT-06 | Testes/evidências fictícios que comprovam controles | I; sem dados reais |

O ator adversarial atual é um cliente HTTP com acesso ao serviço local. Profissional, recepção e administrador são papéis do domínio ainda não autenticados. O laboratório só será consumidor implementado no Ex. 7. Não existe portal/prontuário de paciente; o paciente autenticado citado no Ex. 8 permanece uma **decisão a definir**.

| Componente analisado | Localização e limites |
| --- | --- |
| P-01 — API JSON | `app/routes/consultas.py`, schemas Pydantic; recebe F-01, devolve F-02 e chama P-03 por F-03/04 |
| P-02 — agenda HTML | `app/routes/agenda.py`, templates; recebe F-05, devolve F-06 e lê P-03 por F-07/08 |
| P-03 — acesso a dados | `app/database/consultas.py`; lê/grava D-01 por F-09/10, com lock em `memoria.py` |

**TB-01** separa clientes externos do processo API. **TB-02** marca redução de divulgação entre entidade interna e contrato de saída; é lógica, sem isolamento de processo. Todos os P estão no mesmo processo. P-03 não tem endpoint próprio; ameaças remotas chegam por P-01/P-02, não por uma conexão de banco inventada. TB-03 (laboratório) e TB-04 (banco separado, conforme escolha) são futuras.

## 3. Superfícies de ataque

| ID | Superfície real ou futura | Dados / fluxos / fronteiras | Pontos de atenção |
| --- | --- | --- | --- |
| SUP-01 | POST/PATCH `/consultas` | IDs, horário, motivo, notas e status; F-01/03/09, TB-01 | Falta identidade/vínculo; status livre; validação parcial |
| SUP-02 | GET `/consultas`, GET/DELETE/PATCH por ID | ID/filtros, registros e operação; F-01/02/03/04, TB-01/02 | Identificadores previsíveis; filtros não autorizam; notas da entrada continuam sensíveis |
| SUP-03 | GET `/agenda?dia=...` e conteúdo HTML | Dia, IDs, horário e status; F-05–08, TB-01/02 | Leitura sem identidade; escape e minimização existentes; consultas do dia sem paginação |
| SUP-04 | Depósito/contador e funções Python | Entidades completas; F-09/10, D-01 | Estado volátil, lock local, sem auditoria/constraints de domínio |
| SUP-05 | Respostas de erro e transporte local | Entrada inválida/erros; F-02/06, TB-01 | Reflexão sensível a verificar; HTTP local não prova TLS de deploy |
| SUP-06 | `/`, `/docs`, `/redoc`, `/openapi.json` | Estado e descrição de contratos; não acessam D-01 | Não interpretar documentação ou cadeado futuro como prova de controle; política de exposição a definir no deploy |
| SUP-07 — futura | Login, JWT, rota administrativa | Novos fluxos a desenhar no Ex. 6 | Token, MFA, papel e expiração ainda não implementados |
| SUP-08 — futura | Token M2M e disponibilidade | TB-03; fluxos ainda a criar | Escopos e separação de identidade humana/M2M |
| SUP-09 — futura | Persistência SQLModel | TB-04 conforme topologia; F-09/10 serão atualizados | Query parametrizada, sessão, credenciais e invariantes |

## 4. Misuse cases

Cada resultado proibido descreve o contrato seguro esperado, mesmo quando o incremento atual ainda não tem o controle. Os cenários são planos de análise/teste; não foram executados nesta etapa.

| ID / ator | Precondição | Ação abusiva | Resultado proibido / ameaça | Fluxos / fronteira | Mitigação e verificação |
| --- | --- | --- | --- | --- | --- |
| MU-001 — cliente sem identidade | Serviço acessível; criação aceita IDs numéricos | Enviar `profissional_id` de terceiro e paciente sem vínculo | Atribuir atendimento a profissional que não realizou a ação; TM-001/003 | F-01/03/09, TB-01 | CTRL-01/02; TEST-04/08: exigir identidade e negar vínculo alheio, permitindo vínculo legítimo |
| MU-002 — cliente sem direito de leitura | Existe consulta fictícia com ID conhecido/previsível | Ler por ID, variar filtro ou abrir agenda de outro dia | Conhecer dados clínicos/agenda fora da permissão; TM-002 | F-01/02/05/06, TB-01/02 | CTRL-02; TEST-07/09: dono/recepção permitidos conforme matriz; outro usuário negado/filtrado |
| MU-003 — cliente sem direito de gestão | Existe consulta alvo | PATCH de status/motivo/notas ou DELETE de ID alheio | Alteração/remoção indevida; TM-003 | F-01/03/09, TB-01 | CTRL-02; TEST-07/17: negar antes de ler dados protegidos ou gravar; estado permanece igual |
| MU-004 — cliente manipulando domínio | Entrada passa pela tipagem básica | Criar com IDs não vinculados ou PATCH com status não previsto | Estado inconsistente após definir regras de domínio; TM-006/009 | F-01/03/09, TB-01 | CTRL-05/08; TEST-08/12/16 conforme regra aprovada; não presumir conflito ainda não definido |
| MU-005 — cliente enviando HTML malicioso | Status textual é armazenável | PATCH com `<script>alert(1)</script>`; depois abrir agenda | Texto virar script e atuar no navegador da recepção; TM-005 | F-01/09/08/06, TB-01/02 | CTRL-04; TEST-03 histórico já mostra bloqueio; manter texto comum e payload como texto |
| MU-006 — autor negando alteração | PATCH/DELETE são aceitos; só há datas atuais | Alterar/remover e negar responsabilidade | Não conseguir atribuir ação relevante; TM-007 | F-01/03/09, TB-01 | CTRL-06; teste proposto TEST-19, correlacionando ator/ação/resultado sem registrar segredo |
| MU-007 — cliente abusando do volume | Sem limite de registros/requisições/lista | Repetir criações e leituras amplas, inclusive agenda | Esgotar recursos e impedir atendimento legítimo; TM-008 | F-01/02/05/06/09, TB-01 | CTRL-07; teste limitado TEST-20; parâmetros a justificar, sem ataque de carga nesta etapa |
| MU-008 — incidente operacional | Consultas somente no processo em memória | Reiniciar o processo ou distribuir uso entre workers | Perda de consultas ou visões divergentes; TM-010 | D-01, F-09/10 | CTRL-08; TEST-21 proposto para durabilidade/recuperação; não alegar que cliente HTTP pode reiniciar o host |
| MU-009 — cliente provocando erro | Campo inválido inclui texto fictício sensível | Solicitar validação com dados rejeitados | Repetir dados clínicos no erro/log além do necessário; TM-011 | F-01/02, TB-01 | CTRL-09; TEST-22 proposto; resultado depende de verificar handler efetivo |
| MU-010 — cliente humano elevando privilégio, futuro | Login/rota admin implementados no Ex. 6 | Usar JWT inválido, papel indevido ou pular MFA | Acesso administrativo sem autorização; TM-013 | SUP-07; novos fluxos pendentes | CTRL-01/02; TEST-04/05/06/10, incluindo caminho permitido |
| MU-011 — laboratório, futuro | Client Credentials implementado no Ex. 7 | Pedir privilégio humano ou usar token M2M no CRUD | Ler pacientes/notas ou escrever consultas; TM-014 | SUP-08, TB-03 futura | CTRL-10; TEST-11 positivo de disponibilidade e negativo de escrita/acesso clínico |
| MU-012 — cliente com payload SQL, futuro | Query relacional implementada no Ex. 11 | Inserir payload como valor de busca/filtro | Alterar estrutura da query e ampliar leitura; TM-015 | SUP-09, F-09/10 futuros | CTRL-08; TEST-13 com banco real, mantendo conjunto autorizado e integridade |

Exemplos de IDs e payloads são didáticos e devem usar exclusivamente dados fictícios. MU-002/003 são cenários de acesso por objeto; a demonstração BOLA de **paciente autenticado** exigida no Ex. 8 não está concluída por identificar acesso anônimo agora. Não existe campo `profissional_id` editável no PATCH atual: a tentativa de mudar vínculo deve ser analisada na criação e em qualquer futura operação que realmente permita essa mudança.

## 5. STRIDE nos três componentes reais

As seis categorias foram examinadas em cada P. Propagação de uma ameaça entre componentes não implica uma nova interface de rede nem um finding distinto. Quando a identidade/privilégio ainda não existe, o cenário de falsificação de token/escalada entre papéis é identificado como futuro.

| Componente | Categoria | Cenário contextual / Threat ID | Controle existente e limite |
| --- | --- | --- | --- |
| P-01 | S | IDs declarados na criação podem ser confundidos com identidade de quem age; TM-001. Token falso: TM-013 futuro | Tipar ID não autentica; sem identidade verificada |
| P-01 | T | PATCH/DELETE sem controle do recurso e criação com vínculo indevido; TM-003/006 | Validator de nulos cobre parte da integridade estrutural, não autorização |
| P-01 | R | Mudança não possui ator/histórico atribuível; TM-007 | Datas internas não comprovam autoria e DELETE remove registro |
| P-01 | I | Leitura indevida, regressão de campos internos e erro sensível; TM-002/004/011 | `ConsultaResponse` cobre campos de sucesso; leitura sem autorização e erros ficam abertos |
| P-01 | D | Criação/listagem sem limites de volume; TM-008 | Alguns limites por campo; sem quota/paginação, capacidade não medida |
| P-01 | E | Cliente alcança gestão que deveria exigir profissional/vínculo; TM-003. Admin: TM-013 futuro | Controle de permissão ausente; nenhum JWT/endpoint admin atual |
| P-02 | S | Navegador não comprova identidade de recepcionista; TM-001 | Rota dita “interna” continua sem autenticação |
| P-02 | T | Status persistido tenta mudar semântica da página; TM-005 | Auto-escape impede criar marcação nos casos já testados |
| P-02 | R | Leitura da agenda não é atribuída a usuário; TM-007 | Sem auditoria de acesso; registro futuro deve minimizar informação |
| P-02 | I | Agenda inteira por dia sem autorização e risco de ampliar contexto; TM-002/004 | Projeção elimina clínica/notas, mas IDs/horários ainda são sensíveis |
| P-02 | D | Leitura diária percorre/ordena conjunto em memória sem limite; TM-008 | Filtro de dia não limita esforço total; sem teste de carga |
| P-02 | E | Consumidor alcança leitura reservada à recepção; TM-002. Execução no navegador: TM-005 | Minimização e escape existentes não verificam papel |
| P-03 | S | Dados recebidos de P-01 não carregam identidade verificada do autor; TM-001 | Não há endpoint independente: ameaça propaga a entrada externa, não spoofing de serviço remoto |
| P-03 | T | Escrita sem política de vínculo e invariantes de agenda pendentes; TM-003/006/009 | Lock protege operação local, não ownership nem exclusividade de intervalos |
| P-03 | R | Entidade atual não guarda histórico/ator; TM-007 | `criado_em`/`atualizado_em` não são auditoria suficiente |
| P-03 | I | Entidades completas retornam à apresentação e precisam ser reduzidas; TM-004 | Retorno completo interno é necessário, sem prova de isolamento; filtragem ocorre em P-01/P-02 |
| P-03 | D | Crescimento/lock local, reinício e múltiplos workers; TM-008/010 | Sem durabilidade ou coordenação distribuída |
| P-03 | E | Operação sem autorização em P-01 chega privilegiada à gravação; TM-003 | Módulo não cria barreira independente; acesso ao host/processo está fora do ataque HTTP modelado |

Injeção SQL não se aplica ao depósito atual: não há SQL. Falsificação de JWT, bypass de MFA e scope M2M não são ataques executáveis contra recursos inexistentes. Esses cenários aparecem apenas na extensão futura do modelo.

## 6. Catálogo consolidado de ameaças

Prioridade é uma **recomendação de engenharia qualitativa**, não CVSS ou critério de gate. **P1:** acesso/alteração clínica ou perda de serviço/dados que impede uso seguro. **P2:** risco delimitado/hipótese dependente de verificação ou mitigação de regressão. A prioridade futura deve ser recalculada quando existir o componente. CVSS, impacto de negócio detalhado e security gate pertencem ao Ex. 12.

| ID | Ativos / componente / superfície | Ameaça e STRIDE | Fluxos / fronteira / CIA de origem | Impacto / prioridade | Controle e estado |
| --- | --- | --- | --- | --- | --- |
| TM-001 | AT-01/04; P-01/02/03; SUP-01/03 | Agir sem identidade ou atribuir criação por ID declarado; S | F-01/03/05/09, TB-01; CIA-02/05; LAC-01 | Autoria falsa e acesso ilegítimo; P1 | CTRL-01/02 planejados; lacuna observada |
| TM-002 | AT-01/02; P-01/02; SUP-02/03 | Leitura por objeto/listagem/agenda fora da permissão; I/E | F-01/02/05/06, TB-01/02; CIA-02; LAC-01 | Divulgação clínica e de agenda; P1 | CTRL-02 planejado; minimização parcial CTRL-03/04 |
| TM-003 | AT-01/02/03; P-01/03; SUP-01/02/04 | Gerenciar consulta sem direito ao paciente/recurso; T/E | F-01/03/09, TB-01; CIA-05; LAC-01 | Alteração/remoção de atendimento e notas; P1 | CTRL-02 planejado; lacuna observada |
| TM-004 | AT-02/03/04; P-01/02/03; SUP-02/03/04 | Regressão expõe entidade completa ou amplia contexto; I | F-04/08/02/06, TB-02; CIA-01/02 | Divulgação interna por mudança de contrato; P2 | CTRL-03/04 implementados e verificados historicamente no Ex. 2 |
| TM-005 | AT-01/05; P-02; SUP-01/03 | Texto persistido interpretado como HTML ativo; T/I/E | F-01/09/08/06, TB-01/02; CIA-03 | Alterar página e afetar sessão futura; P2 no contexto testado | CTRL-04 verificado no Ex. 2; não há bypass demonstrado |
| TM-006 | AT-01/02; P-01/03; SUP-01/04 | Status/vínculo semanticamente inválido aceito; T | F-01/03/09; CIA-04; LAC-02 | Estado incoerente ou vínculo indevido; P1 para vínculo, P2 para catálogo a definir | CTRL-05 parcial; CTRL-02/08 planejados |
| TM-007 | AT-01/03/04; P-01/02/03; SUP-01–04 | Leitura/alteração sem atribuição suficiente; R | F-01/05/09; CIA-05; LAC-06 | Dificuldade de investigação e responsabilização; P2 | CTRL-06 planejado; ausência observada, sem alegação de não repúdio |
| TM-008 | AT-05; P-01/02/03; SUP-01–04 | Volume consome memória/CPU e serializa atendimento; D | F-01/02/05/06/09; CIA-08; LAC-03 | Indisponibilidade; P1 se exposto a múltiplos consumidores | CTRL-07 planejado; capacidade não medida |
| TM-009 | AT-01; P-03/D-01; SUP-04 | Agenda viola regra de conflito ainda não definida; T | F-09/10; CIA-06; LAC-04 | Atendimento inconsistente; prioridade a definir com regra | CTRL-08 futuro/condicional; sem regra não afirmar uma vulnerabilidade de sobreposição demonstrada |
| TM-010 | AT-01/05; P-03/D-01; SUP-04 | Reinício perde estado ou workers divergem; D/T | F-09/10; CIA-07; LAC-04 | Perda/indisponibilidade da agenda; P1 antes de dados reais | CTRL-08 planejado; consequência estrutural da memória |
| TM-011 | AT-02/03; P-01/02; SUP-05 | Erro/log inclui dados sensíveis da entrada; I | F-01/02/05/06, TB-01; LAC-06 | Divulgação por caminho de falha; P2 até verificar | CTRL-09 planejado; hipótese, sem experimento nesta etapa |
| TM-012 | AT-01/02/03; TB-01; SUP-05 | Interceptar/alterar tráfego HTTP em topologia exposta; S/T/I | F-01/02/05/06; LAC-05 | Dados/identidade em trânsito comprometidos; P1 para deploy sem TLS | CTRL-11 futuro/condicional; HTTP em loopback não comprova ataque externo |

### Extensão futura explicitamente separada

| ID | Ativo / componente futuro | Ameaça / STRIDE | Mitigação / teste / momento |
| --- | --- | --- | --- |
| TM-013 | Identidade humana, sessão e operação administrativa; SUP-07 | JWT fora do contrato, papel indevido ou MFA contornado; S/E | CTRL-01/02: bcrypt, validação JWT/claims/expiração, política e MFA simulado; TEST-04/05/06/10; Ex. 6/9 |
| TM-014 | Identidade M2M e disponibilidade; SUP-08/TB-03 | Token de parceiro obtém poder humano ou lê saúde; S/I/E | CTRL-10: Client Credentials, tipo/audiência/escopos distintos e autorização; TEST-11; Ex. 7 |
| TM-015 | Banco relacional e dados clínicos; SUP-09/TB-04 conforme topologia | Entrada muda estrutura SQL; T/I | CTRL-08: parametrização, sessão e allowlist de estrutura; TEST-13 com banco real; Ex. 9 quando viável e Ex. 11 |
| TM-016 | Login e capacidade do serviço; SUP-07 | Adivinhação de credenciais e abuso automatizado; S/D | CTRL-01/07: verificação segura, limite de login diferenciado, erros sem enumeração; TEST-04/14; Ex. 6/10 |

AT-01–06 continuam descrevendo apenas o estado atual. Ativos, processos e fluxos novos receberão IDs quando implementados. Ameaças futuras não provam funcionamento dos controles; não fazem JWT/SQL aparecer retroativamente no DFD.

## 7. Mitigações, responsabilidade e risco residual

Responsável pela implementação/revisão: aluno desenvolvedor. Aceitação de risco e liberação final serão justificadas no Capstone; esta priorização não aprova deploy.

| Controle | Ação concreta e local esperado | Estado / incremento | Risco residual ou decisão necessária |
| --- | --- | --- | --- |
| CTRL-01 | Identidade centralizada, bcrypt, JWT expirável, claims e MFA administrativo simulado | Planejado Ex. 6; middleware JWT Ex. 9 | Política de token/MFA a definir; autenticação não comprova direito ao objeto |
| CTRL-02 | Autorização por recurso/vínculo antes de leitura/escrita; escopo de listas/agenda e negação por padrão | Planejado Ex. 6/9, futura camada de autorização compartilhada | Matriz de permissões, paciente autenticado e vínculo exigem decisão; administrador não ganha dados clínicos automaticamente |
| CTRL-03 | `ConsultaResponse` nas quatro respostas JSON e revisão da allowlist | Implementado `app/models/consultas.py`, `app/routes/consultas.py`; TEST-02 histórico | Novos campos/erros precisam de revisão; dados públicos do contrato ainda exigem autorização |
| CTRL-04 | Contexto HTML mínimo, herança e auto-escape sem `safe` | Implementado `app/routes/agenda.py`, templates; TEST-03 histórico | Não cobre JS/CSS/DOM de frontend inexistente; IDs continuam pessoais e agenda precisa de autorização |
| CTRL-05 | Tipos, limites e validator; acrescentar `extra='forbid'`, allowlist/regex e semântica onde definidos | Parcial em schemas; expansão Ex. 9 | Extras ignorados não provam mass assignment; status livre requer regra; regex não substitui escape/SQL seguro |
| CTRL-06 | Auditoria mínima com ator, ação, alvo mínimo, instante e resultado; proteção/retenção a definir | Recomendação de engenharia derivada de TM-007, integrada Ex. 6/9/11 conforme desenho | Não gravar tokens, senhas, notas completas; logs não garantem não repúdio ou conformidade |
| CTRL-07 | Limite diferenciado no login; definir limites de requisição/volume/listagem por risco | Ex. 10 exige login; demais limites são recomendações de engenharia | Contadores em memória não coordenam workers; parâmetros/capacidade precisam de verificação |
| CTRL-08 | SQLModel relacional, queries parametrizadas, sessão/transação/constraints; recuperação conforme regra | Planejado Ex. 11; regras antes de disponibilidade Ex. 7 | Banco, duração, conflito, estados e recuperação a definir; rollback/teste real, não apenas mocks |
| CTRL-09 | Tratar erros sem dados sensíveis e revisar observabilidade | Recomendação de engenharia ligada a TM-011 | Verificar comportamento HTTP efetivo antes de afirmar sanitização; não esconder falhas inesperadas |
| CTRL-10 | Separar token humano/M2M e escopos mínimos de disponibilidade | Planejado Ex. 7 | Token válido não autoriza CRUD nem acesso clínico |
| CTRL-11 | Definir HTTPS/topologia; CORS explícito e headers HSTS/X-Frame-Options/X-Content-Type-Options | Headers/CORS Ex. 10; HTTPS é decisão de implantação | HSTS depende de HTTPS; CORS não impede cliente HTTP direto ou substitui autorização |

## 8. Estratégia de testes derivada do modelo

Cada teste negativo deve ter um caso autorizado/entrada válida correspondente. TEST-01–18 identificam os cenários funcionais e de segurança do projeto descritos nesta seção; TEST-19–22 são recomendações adicionais rastreáveis. “Proposto” não significa executado ou obrigatório por si só. Ferramenta padrão é pytest HTTP; unidade com mocks só verifica coordenação, não transação/concorrência.

| Threat ID | Endpoint / cenário | Teste e comportamento esperado | Ferramenta / estado / evidência |
| --- | --- | --- | --- |
| TM-004 | POST/GET/lista/PATCH de consultas | TEST-02: entidade mantém campos internos; JSON contém somente seis campos autorizados | pytest HTTP; **verificado Ex. 2**; teste `test_respostas_excluem_campos_internos_sem_apagar_armazenamento`, JSON/pytest em `evidencias/ex02/` |
| TM-005 | PATCH status → `/agenda` | TEST-03: texto normal preservado; script e imagem/handler viram texto, sem tags ativas | pytest HTTP/parsing HTML; **verificado Ex. 2**; `test_agenda_escapa_texto_malicioso_armazenado`, payload/HTML/PNG |
| TM-001/013/016 | Login e rotas protegidas futuras | TEST-04/05: credencial válida permite; token ausente/inválido/expirado, claim/tipo/audiência indevidos não permitem | pytest HTTP/relógio controlado; proposto Ex. 6/7/12 |
| TM-013 | Rota administrativa futura e MFA | TEST-06/10: administrador com segundo fator válido permite; papel comum/fator pendente ou inválido nega | pytest HTTP; proposto Ex. 6/12; rota a definir |
| TM-002/003 | GET/PATCH/DELETE por ID | TEST-07: mesmo ator autorizado permite; outro proprietário é negado e não recebe dado nem altera estado | pytest HTTP; proposto Ex. 6/8/9/13; caso de paciente Ex. 8 depende da decisão de acesso |
| TM-001/003/006 | POST consulta e mudança de vínculo se existir | TEST-08: profissional só opera sobre paciente vinculado; identidade do corpo não amplia poder | pytest integrado; proposto Ex. 6/9/11 |
| TM-002/004 | Listagem/filtros e agenda | TEST-09: lista só inclui recursos permitidos; recepção recebe mínimo; dia/filtro não contorna política | pytest HTTP; proposto Ex. 6/12; testes atuais de minimização não comprovam autorização |
| TM-014 | Token M2M e disponibilidade futura | TEST-11: scope correto permite disponibilidade; falta/excesso/tipo indevido e escrita/acesso clínico negados | pytest HTTP; proposto Ex. 7/12 |
| TM-006 | Corpos, filtros e dia | TEST-12: válido aceito; extra/nulo/tipo/limite/status proibido rejeitados conforme contrato | pytest unitário + HTTP; **parcial histórico**: nulos PATCH/data inválida; extras/allowlists propostos Ex. 9/13 |
| TM-015 | Query relacional futura | TEST-13: payload permanece valor ou é rejeitado, sem ampliar resultado autorizado ou alterar dados | pytest com banco real; proposto Ex. 11/13, Ex. 9 se existir SQL |
| TM-016/008 | Login futuro e rota comum | TEST-14: uso abaixo do limite permite, excesso retorna bloqueio; regra de login é mais restritiva | pytest HTTP/relógio controlado; proposto Ex. 10/12 |
| TM-012/005 | JSON/HTML/erros e origens | TEST-15: headers exigidos, CORS permitido/rejeitado e preflight corretos; HTTPS verificado no ambiente definido | pytest HTTP, inspeção TLS e ZAP passivo Ex. 13; proposto Ex. 10/13; headers não fecham sozinhos TM-005/012 |
| TM-009 | Gravação de agenda relacional | TEST-16: após definir regra, concorrência respeita invariante e falha faz rollback | pytest com banco real; proposto Ex. 11; não usar unicidade de início como prova de não sobreposição |
| TM-003 | Coordenação de autorização/persistência | TEST-17: mock de gravação/leitura protegida não é chamado quando autorização falha; sucesso autorizado chama | pytest unitário com mocking; proposto Ex. 13 |
| TM-001/004/013/014 | `/openapi.json` versus execução | TEST-18: schemas/segurança/escopos documentados correspondem ao HTTP real | pytest + revisão; proposto Ex. 13; não há security scheme atual |
| TM-007 | Leitura/mutação conforme política de auditoria | TEST-19: sucesso/negação possuem ator/ação/resultado mínimos, sem segredo ou notas completas | pytest/captura de auditoria; proposto após CTRL-06; retenção/proteção a definir |
| TM-008 | Limites de volume/listagem | TEST-20: volume limitado produz comportamento definido e não entrega lista ilimitada; caminho normal preservado | pytest HTTP e medição controlada; proposto após parâmetros, sem metas arbitrárias |
| TM-010 | Reinício/recuperação do banco escolhido | TEST-21: persistência/recuperação atendem decisão e não misturam bancos de teste/reais | integração em ambiente isolado; proposto Ex. 11; não executado |
| TM-011 | Entradas inválidas e erros | TEST-22: erro útil não repete nota/motivo/token sensível; erro inesperado permanece investigável sem stack trace ao cliente | pytest HTTP/captura de logs; proposto após verificar handler; não executado |

TEST-01 continua regressão funcional do CRUD, sem ameaça presumida. As evidências históricas referidas não foram reexecutadas nesta etapa. Nenhum teste de abuso, concorrência, JWT, M2M, SQL ou ZAP foi executado no Ex. 4.

## 9. Evolução, fechamento e rubrica

- **Ex. 5:** posicionar CTRL nos módulos e fronteiras, relacionando design, implementação e infraestrutura aos TM existentes.
- **Ex. 6/7:** atualizar DFD, papéis/atributos/ownership, ativos de identidade e cenários futuros; registrar testes reais de CTRL-01/02/10.
- **Ex. 8/9:** localizar fraquezas demonstráveis, preservar estado anterior e vincular finding → TM → correção → mesma tentativa antes/depois. Não remover escape para fabricar XSS.
- **Ex. 10/11:** implementar hardening/persistência e reavaliar D-01/fluxos, concorrência, erros e disponibilidade.
- **Ex. 12/13:** usar esta matriz para testes, CVSS/impacto/gate e relatório final; registrar cobertura parcial, risco residual e decisão de liberação.

**Regra de manutenção:** conservar IDs TM mesmo após mitigação. Para fechar uma ameaça, registrar controle/localização, versão, teste/evidência de execução e risco residual. Uma threat mitigada no HTML não fecha o acesso clínico indevido no JSON; um teste mocked não fecha garantia de banco real.

| Critério | Demonstração neste relatório | Evidência de entrega |
| --- | --- | --- |
| R07 | Misuse cases com ator, precondição, tentativa, resultado proibido, fluxo e controle/teste | Seção 4; versão inicial em `evidencias/ex04/threat-model-v1.md` |
| R08 | 18 avaliações STRIDE em três componentes; ativos, superfícies, ameaças, controles e testes ligados por IDs | Seções 2–8, DFD Ex. 3, revisão e baseline Ex. 4 |

- [x] Misuse cases associados a fluxos reais ou explicitamente futuros.
- [x] P-01/P-02/P-03 analisados nas seis categorias STRIDE.
- [x] Ativos, superfícies, controles, testes e riscos residuais rastreados.
- [x] Controles existentes, hipóteses e implementação futura separados.
- [x] REQ-04/R07–R08 documentados, com snapshot inicial para comparação no Ex. 12.

Verificações documentais e evidências: [Exercício 4](../evidencias/ex04/README.md). Esta versão não declara vulnerabilidades exploradas, scanner executado, CVSS atribuído, conformidade LGPD ou autorização para deploy.
