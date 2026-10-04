# Revisão manual de vulnerabilidades — Exercício 8

## Resultado e limites da entrega

Foram identificados três padrões de categorias distintas do **OWASP Top 10:2021**: VUL-001/A01 (histórico real), VUL-002/A05 e VUL-003/A07 (baseline Ex. 8). Este relatório preserva aquela revisão; a evolução no Ex. 10 aparece ao final. A autorização do histórico já foi corrigida no Ex. 6. A edição 2021 foi fixada para consistência; não é apresentada como a mais recente nem como edição imposta pela disciplina.

O requisito R13 pede revisão manual de pelo menos três categorias e inclui BOLA; R14 envolve identificação e posterior correção centralizada. O cenário normativo cita paciente autenticado acessando prontuário alheio. **A aplicação real não tem papel de paciente nem prontuário**: oferece consultas e três papéis internos. Um laboratório não é substituto desse paciente.

**Decisão aprovada pelo responsável pelo projeto:** preservar a falta de autorização por objeto realmente existente no histórico e acrescentar um experimento didático separado com dois pacientes autenticados. Não adicionar portal/papel de paciente na API final. **Aceitação acadêmica pendente:** a demonstração isolada não é finding da aplicação e não comprova que aquele cenário existia no histórico. A revisão técnica foi executada; não declarar conclusão integral do requisito de paciente até validar essa interpretação com a orientação da disciplina.

| Finding | Categoria 2021 | Estado | Evidência |
| --- | --- | --- | --- |
| VUL-001: consulta por ID sem autorização por objeto | A01 Broken Access Control; relação com API1:2023 BOLA | Encontrado/reproduzido no histórico; controle atual verificado | `historico.json` e negativas em `atual.json` |
| VUL-002: respostas sem headers de segurança | A05 Security Misconfiguration | Aberto no baseline atual; hardening previsto no Ex. 10 | Headers ausentes em HTML autenticado e erro 401 |
| VUL-003: login sem throttling | A07 Identification and Authentication Failures | Aberto no baseline atual; rate limiting previsto no Ex. 10 | Vinte erros 401 e login correto 200 sem espera imposta |

BOLA é a nomenclatura específica do **OWASP API Security Top 10, API1:2023**, relacionada a A01:2021. As listas são distintas. XSS e SQL Injection seriam ambos A03:2021, não duas categorias. Nesta revisão eles não são findings explorados.

## Método, versões e fontes inspecionadas

- Baseline atual: `c68979a6242e8772627f03def1a8ea565e715dae` (merge do Ex. 7).
- Histórico real: `4d6d7e342ac3b64e621a4c4d5a60018022e0433b` (incremento Ex. 2 anterior à autenticação).
- 41 snapshots de fontes com revisão/SHA-256 em `evidencias/ex08/manifesto.json`: 29 arquivos da aplicação atual e 12 arquivos do baseline histórico para reprodução autossuficiente, inclusive sem Git na entrega.
- Leitura dos caminhos HTTP → dependência/principal → política/recurso → memória → serialização/Jinja2. As localizações das conclusões são explicitadas abaixo; o manifesto permite recuperar a linha daquele baseline sem depender da evolução futura.
- Inventário de 14 operações OpenAPI, mais superfícies auxiliares, em `evidencias/ex08/rotas.json` e inventário manual abaixo. A metadata não comprova segurança; os percursos relevantes foram exercitados com TestClient.
- Reprodução em subprocessos/armazenamentos separados, sem servidor externo. Credenciais/JWT/chave/hash são fictícios e efêmeros, sem armazenamento em evidências. Nenhum scanner, SAST, ZAP ou teste de carga foi executado.

### Inventário manual das fronteiras

| Operação | Entrada / destino sensível | Controle verificado no código / saída |
| --- | --- | --- |
| POST `/consultas` | IDs/data/motivo/notas → criação em memória | Profissional e vínculo confiável antes de gravar; response model exclui notas/auditoria |
| GET `/consultas` | Filtros paciente/profissional → listagem | Restrição por profissional + vínculo; filtro não amplia acesso |
| GET/PATCH/DELETE `/consultas/{id}` | ID e atualização parcial → registro existente | `consulta_autorizada` central; papel, profissional e vínculo antes da leitura externa/mutação |
| GET `/agenda` | Dia → snapshot diário → HTML | Principal comum, papel de recepção, cookie somente aqui, contexto mínimo e auto-escape; headers de proteção ausentes |
| POST `/auth/token` | Form password → conta/bcrypt → JWT ou desafio | Hash, conta ativa e erro sem enumeração; nenhum contador/janela de login |
| POST `/auth/mfa` | Desafio/código → estado temporário → JWT admin | Expiração, uso único, cinco erros por desafio; entrada extra forbid; novo login renova desafio, não é limite global |
| POST/DELETE `/auth/agenda-session` | Bearer recepção → cookie criar/apagar | Papel, HttpOnly/Secure por padrão/SameSite Strict/path; não há autenticação por cookie nessas mutações |
| POST `/auth/m2m/token` | Basic + grant/scope → token do cliente | Cliente confiável/hash, grant fixado, scope máximo e ausência/vazio distintos; sem rate limiting global |
| GET `/disponibilidade` | Bearer cliente + dia/profissional → intervalos | Audiência/tipo/subject/client/scope; sem pacientes ou motivo; leitura não reserva horário |
| GET `/admin/status` | Bearer humano → diagnóstico | Papel admin e MFA no principal; sem dados clínicos |
| GET `/` | Status estático | Público, sem leitura de dados clínicos |
| GET `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` | Metadata/interface/documentação | Públicos por configuração; acesso público à documentação não foi classificado automaticamente como vulnerabilidade |

## VUL-001 — Falha histórica de autorização por objeto (A01)

**Localização:** snapshot histórico `app/routes/consultas.py`, linhas 54–61 (`endpoint_obter_consulta`), 71–78 (PATCH) e operação DELETE; `app/database/consultas.py`, lookup por identificador. O endpoint recebe somente o ID, resolve registro e retorna/muta sem principal ou comparação com proprietário. O schema de saída controla campos, mas não decide quem pode ver a consulta.

**Causa:** falta de autorização por recurso. IDs previsíveis tornam enumeração fácil; trocar por UUID não resolveria o controle ausente. A ausência de autenticação é registrada como precondição do histórico, não escondida para alegar um paciente logado inexistente.

**Exploração reproduzida no código real do histórico:** criar consultas fictícias dos pacientes 1 e 2; GET `/consultas/1` e depois `/consultas/2`, alterando apenas ID; ambos retornam 200, incluindo motivo do outro registro. PATCH `/consultas/2` sem identidade altera o motivo e retorna 200. `historico.json` guarda três respostas reais. Não havia uma permissão validada que limitasse o chamador ao primeiro registro.

**Impacto observado:** divulgação de vínculo/motivo de consulta e escrita indevida. Não foi acessado prontuário real ou dado de terceiros. **Categoria:** A01:2021; correspondência de ausência de controle no lookup por objeto com API1:2023 BOLA. O rótulo histórico não representa sucesso de paciente autenticado, que só aparece no experimento didático abaixo.

**Estado atual:** `app/auth/policies.py:26` (`consulta_autorizada`) combina papel, profissional do recurso e vínculo; `pode_acessar` está na mesma camada. O teste exploratório atual confirma leitura do dono 200, leitura/PATCH/DELETE cruzados 404, anônimo 401 e estado intacto. Não se reintroduziu a falha nas rotas.

**Correção/reutilização proposta:** manter política central, inclusive em listagens/criação; integrar o middleware exigido no Ex. 9 sem substituir ownership por token válido. Payloads de ID/mutação são preservados para antes/depois, reconhecendo que a primeira mitigação foi Ex. 6. Regressão: dono autorizado continua funcionando; outro proprietário não lê nem modifica; vínculo ausente nega mesmo se profissional_id parecer correto. TM-002/003, CTRL-01/02, TEST-07/08/09; R13 e parte identificável de R14.

### DEMO-001 — Pacientes autenticados, experimento didático autorizado

Em `evidencias/ex08/reproduzir.py`, função `didatico`, uma aplicação FastAPI local **não importada por `app/main.py`** contém dois registros clínicos fictícios e valida JWT de paciente. O GET deliberadamente ignora o paciente autenticado ao resolver o ID. Para cada uma das duas identidades, leitura própria retorna 200 e, mantendo o mesmo bearer e trocando somente o ID, leitura alheia também retorna 200. Quatro observações em `didatico.json`.

Isso ensina a diferença entre autenticação e ownership com o ator do cenário acadêmico. O experimento não integra a suíte final, não é served por Uvicorn, não modifica a aplicação e não é contado como quarta categoria/finding real. Não foi apresentada correção didática nesta etapa. Aceitação para cumprir o cenário normativo permanece pendente; não confundir autorização do responsável para o experimento com aceite da disciplina.

## VUL-002 — Headers de proteção ausentes (A05)

**Localização:** `app/main.py:26–39`, composição sem middleware de segurança; `app/routes/agenda.py`, resposta HTML aplica apenas Cache-Control. O snapshot completo permite verificar também que auth/erro não acrescenta os headers exigidos para o hardening.

**Causa:** aplicação não configura `X-Frame-Options`, `X-Content-Type-Options` ou `Strict-Transport-Security`; tampouco CSP frame-ancestors como proteção alternativa de enquadramento. A presença de HttpOnly/SameSite não define esses headers.

**Reprodução:** GET `/agenda?dia=2026-10-15` com bearer válido da recepção retorna HTML 200 com os quatro headers verificados ausentes; GET de consulta sem token retorna 401 também sem eles. `atual.json` registra nomes/valores observados. A requisição é uma inspeção da configuração efetiva, não um payload que comprova roubo de sessão.

**Impacto e alcance:** faltam proteções de navegador contra enquadramento e sniffing e política de transporte estrito para eventual HTTPS. Exploração por clickjacking/sniffing/interceptação depende de navegador, origem, tipo de conteúdo e topologia. **Não foi executado ataque de iframe, interceptação ou HTTPS**. Ausência de HSTS em localhost HTTP é limitação esperada; não basta, isoladamente, para alegar exposição em produção. O finding agrupa o hardening ausente e especialmente a resposta HTML sem política de frame, conforme A05:2021.

**Correção proposta:** Ex. 10 implementará centralmente os três headers exigidos com valores justificados e comportamento em sucesso/erro/autenticação; HSTS pressupõe HTTPS. CSP é recomendação complementar, não requisito adicional imposto aqui. No Ex. 9 a investigação não deve inventar correção de headers como requisito daquele exercício. Regressão: mesmas requisições passam a incluir os valores definidos; browser/TLS reais necessários para comprovar efeitos externos. TM-012, CTRL-11, TEST-15; R13 e preparação de R17.

## VUL-003 — Login sem proteção contra repetição (A07)

**Localização:** `app/routes/auth.py:19–33`, função login verifica senha e emite token/desafio sem limitar frequência/falhas; `app/main.py`, ausência de middleware/limitador. Cinco tentativas em `app/auth/mfa.py` valem somente para um desafio, não para login/senha.

**Causa:** automação de tentativas é processada repetidamente, sem throttling/espera ou regra de rate limiting de login. Mensagem uniforme, hash bcrypt e expiração do bearer não substituem limitação de tentativas. O enunciado de hardening exige esse controle no incremento seguinte apropriado.

**Reprodução limitada:** vinte POST `/auth/token` consecutivos para a mesma conta fictícia, todos com senha incorreta, recebem 401 sem 429/Retry-After. Depois, uma requisição com a senha correta já conhecida recebe 200 imediatamente, sem espera imposta pelo servidor. `atual.json` guarda cada resultado e omite o token do sucesso. O cadastro é efêmero e usa bcrypt custo 12.

**Impacto e alcance:** padrão permite tentativa automatizada de adivinhação; cada verificação também consome CPU. **Não foi descoberta senha, tomada conta, medida capacidade ou provado um volume ilimitado**. Vinte é volume do ensaio, não limiar de política inventado. Não se executou ataque contra serviço externo.

**Categoria:** A07:2021. **Correção proposta:** Ex. 10 definirá e justificará janela/limites/chave de rate limiting, diferenciando login e rotas comuns; aplicar também ao endpoint M2M, sem confiar em proxy não autorizado. Evitar lockout arbitrário que permita negar serviço a outro usuário. Ex. 12 poderá correlacionar alertas/auditoria e gate. Regressão: depois do limiar escolhido, mesma sequência recebe 429/Retry-After e login legítimo permitido conforme janela; relógio controlado, sem sleep nos testes. TM-016/008, CTRL-07, TEST-14; R13 e preparação de R17.

## Observações que não contam como categorias vulneráveis demonstradas

| ID | O que foi verificado | Consequência para Ex. 9 |
| --- | --- | --- |
| OBS-001 | Campo extra `papel=administrador` no POST consulta é ignorado; corpo válido recebe 201, papel não é armazenado/exposto e admin continua 403 | Falta rejeição extra='forbid' no contrato de consultas, a corrigir; **não é mass assignment ou elevação demonstrada** |
| OBS-002 | Status aceita `<script>alert(1)</script>`, mas agenda o escapa para texto | Rejeitar entradas inadequadas com allowlist/regex mantendo escape; **não alegar XSS stored executado** |
| OBS-003 | Dados em dict/lock, sem engine/SQL executável | **Não alegar SQL Injection**; esclarecer ensaio relacional isolado no Ex. 9 ou executar prevenção com SQLModel no Ex. 11 |
| OBS-004 | Duração/agenda calculadas, sem reserva atômica ou constraint de conflito | Risco de consistência já registrado, não um finding novo de categoria inventada |
| OBS-005 | Sem trilha de auditoria persistente e login/M2M sem limite global | Riscos abertos do threat model; não multiplicar categorias sem demonstração específica |

## Plano de continuidade e critério de conclusão

1. Preservar snapshots/payloads/evidência; não converter sucesso de ataque em comportamento esperado de `tests/`.
2. Ex. 9: endurecer entradas e contratos, integrar middleware/ownership, manter encoding, escolher outro endpoint com padrão compartilhado; documentar lacunas SQL/XSS do antes/depois sem fabricar estado vulnerável na API final.
3. Ex. 10: fechar VUL-002/VUL-003 com mesmos cenários e política explicitamente justificada.
4. Ex. 11: validar queries/constraints/consistência no banco real escolhido.
5. Ex. 12/13: atribuir CVSS com vetor/versão e impacto de negócio, definir gate e rastrear cada finding, correção, teste e risco residual. Não atribuído CVSS nesta etapa.
6. Registrar resposta da orientação acadêmica sobre uso de histórico e experimento paciente; reavaliar R13/R14 sem inventar aceite.

- [x] Revisão manual com causas/localizações e três categorias distintas.
- [x] BOLA/lookup por ID histórico preservado; controle atual verificado sem regressão intencional.
- [x] Experimento separado de dois pacientes autenticados autorizado e executado.
- [x] Evidências reais, payloads e rastreabilidade ligados ao threat model.
- [ ] Aceitação acadêmica do experimento como representação do cenário de paciente/prontuário.
- [ ] Correções dos findings abertos e sua regressão, nas etapas responsáveis.

## Referências primárias e classificação

- [OWASP Top 10:2021 A01](https://owasp.org/Top10/2021/A01_2021-Broken_Access_Control/): autorização por recurso e acesso indevido por ID.
- [OWASP API Security Top 10 API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/): BOLA e diferença entre autenticar e autorizar objeto.
- [OWASP Top 10:2021 A05](https://owasp.org/Top10/2021/A05_2021-Security_Misconfiguration/): configuração e headers de segurança ausentes/inadequados.
- [OWASP Top 10:2021 A07](https://owasp.org/Top10/2021/A07_2021-Identification_and_Authentication_Failures/): tentativas automatizadas e falta de proteção de login.

[Evidências do Ex. 8](../evidencias/ex08/README.md) e [rastreabilidade](rastreabilidade.md) registram estado efetivamente observado, propostas e pendências. O relatório não declara liberação para produção ou conformidade regulatória.

## Evolução — Exercício 9

A [análise de correções](correcoes-entrada-saida.md) registra middleware JWT integrado ao ownership, rejeição de extras e allowlists, mantendo intactas as observações históricas acima. OBS-001 agora é rejeitada na criação; PATCH compartilha a correção. OBS-002 agora é rejeitada na entrada de status, e dados legados continuam escapados. VUL-001 permanece mitigada; VUL-002 e VUL-003 continuam abertos para Ex. 10.

**OBS-006 — contrato de formulário M2M:** nova revisão do baseline real preservado verificou `/auth/m2m/token` com Basic válido e `papel=administrador`: 200 e extra ignorado, sem elevação de privilégio. Correção no Ex. 9: modelo de Form com `extra='forbid'` retorna 422; grant/scope permitidos conservam 200. É expansão do padrão OBS-001, não quarta categoria OWASP inventada. Evidência em `evidencias/ex09/m2m-antes.json` e `resultados.json`. A rota estava no inventário, mas não havia sido citada como finding de extras; escolha aprovada, interpretação literal acadêmica pendente.

DEMO-001 ganhou contraparte isolada com ownership; DEMO-002 demonstra SQL concatenado versus parametrizado somente em SQLite fictício. Não reclassificar esses experimentos como vulnerabilidades encontradas em `app/`. Não afirmar exploração/correção de XSS real onde o auto-escape já funcionava.

## Evolução — Exercício 10

VUL-002: DENY/nosniff presentes nas respostas verificadas, HSTS de um ano em HTTPS e CORS explícito. VUL-003: as mesmas 20 tentativas agora recebem 401 nas primeiras cinco e 429 nas demais; credencial conhecida volta a funcionar após a janela. Controles e regressões em [hardening](hardening.md) e `evidencias/ex10/`.

Estado: mitigadas/verificadas no escopo local, com riscos de implantação residuais. HSTS não é enviado em HTTP e HTTPS do TestClient não comprova TLS/browser. Contador não coordena workers nem impede IPs distribuídos; sem CVSS/ZAP ou autorização de deploy. As evidências e os estados do baseline Ex. 8 acima não foram reescritos.
