# Registro de Decisões Técnicas (ADR / Decisões de Projeto)

Este documento registra as decisões arquiteturais e técnicas de maior relevância para o desenvolvimento da API de agendamento de consultas.

## DEC-17: Localização dos controles e partições do Exercício 5

- **Contexto:** a arquitetura precisa localizar as ameaças STRIDE nos componentes/fluxos e nos eixos design, implementação e infraestrutura, preparando a autenticação sem duplicar lógica nas rotas JSON e HTML.
- **Decisão:** manter o mesmo processo modular e DFD; explicitar responsabilidades de transporte, apresentação, identidade, política por recurso, operação/persistência e configuração. JWT valida identidade, enquanto ownership e escopo dependem de recurso/vínculo. Middleware futuro reutilizará o verificador de token; não inferirá ownership somente pela URL.
- **Recomendação de engenharia:** RBAC para papéis internos combinado com política por recurso/atributos de vínculo; justificar o contrato final no Ex. 6 após fechar a matriz. Constraints/transações no banco escolhido complementam validação, sem tratar lock em memória como exclusividade de agenda.
- **Alternativas:** política copiada em cada rota, toda segurança no middleware ou divisão em microserviços. Rejeitadas por duplicação, falta de contexto do recurso ou complexidade sem necessidade. Não criar abstrações ou módulos vazios nesta etapa.
- **Decisões a definir:** relação paciente/profissional e permissões clínicas/admin; transporte de identidade para HTML; claims/expiração e MFA; duração/status/conflito; banco/recuperação; TLS/proxy/origens/hosts/workers. Cookie/sessão exige reavaliar CSRF e não é controle já implementado.
- **Consequências:** doze vetores VD/VI/VF ligados a TM e CTRL no relatório `docs/arquitetura-seguranca.md`; nenhum novo fluxo atual ou fronteira de isolamento presumida. As mitigações continuam nos exercícios correspondentes.
- **Verificação:** inspeção dos fluxos atuais, revisão de acesso permitido/proibido planejado, fonte/diagrama e rastreabilidade R09. Baseline: `e2f239badbaa6905ef32cdfe9423e0fa33b61065`; testes existentes permanecem históricos.

## DEC-16: STRIDE rastreável no Exercício 4

- **Contexto:** o Assessment exige misuse cases e STRIDE em pelo menos três componentes, com ativos, superfícies e mitigações. O DFD do Ex. 3 já identifica os três processos reais P-01/P-02/P-03.
- **Decisão:** analisar as seis categorias em cada processo e consolidar ameaças únicas em `docs/threat-model.md`. Preservar AT/P/F/TB do DFD; introduzir MU/TM/SUP/CTRL e vincular ao catálogo TEST da seção 8 desse documento. Propagação entre módulos não exige inventar interfaces de rede ou duplicar IDs de ameaça.
- **Recomendação de engenharia:** distinguir lacuna observada, mitigação verificada historicamente, hipótese e ameaça futura/condicional. Usar prioridade qualitativa contextual; CVSS e limiar do gate serão definidos no Ex. 12, sem importar um score arbitrário.
- **Alternativas:** analisar somente rotas ou listar STRIDE genérico. Rejeitadas por omitirem processamento HTML, armazenamento e ligação ao fluxo sensível. Não implementar JWT, banco ou mitigações posteriores como parte de um exercício documental.
- **Consequências:** o modelo inicial 1.0 tem 12 misuse cases, 18 avaliações e 16 Threat IDs (12 atuais/condicionais e quatro futuros). Guardar snapshot em `evidencias/ex04/threat-model-v1.md`; futuras atualizações mantêm IDs e registram teste, controle e risco residual. Os TEST-19–22 adicionais são recomendações, não novos requisitos acadêmicos.
- **Verificação:** revisão de correspondência com código/DFD, cobertura dos três componentes, referências e rastreabilidade; testes Ex. 2 permanecem históricos. Baseline da aplicação: `fe31673e1ed4e0238277abe0b111d66be1363c9e`.

## DEC-15: Referenciais e baseline de segurança do Exercício 3

- **Contexto:** o Assessment exige CIA, associação de OWASP/NIST SSDF/MITRE a controles existentes e DFD com fronteiras e fluxos de pacientes; não define edições específicas.
- **Recomendação de engenharia adotada:** fixar OWASP Top 10 2021, API Security Top 10 2023 como complemento, SSDF 1.1 (SP 800-218) e CWE 4.20 conforme as páginas oficiais consultadas. O recorte 2021 mantém a nomenclatura estável; não é apresentado como edição mais recente. CWE é a referência MITRE escolhida para descrever fraquezas de software, sem alegar uso de ATT&CK. Categorias API1/API3 não devem ser confundidas com A01/A03 do Top 10 geral.
- **Decisão:** documentar o estado após o Ex. 2, baseline `46db788b99a19b4cf145555e8e9ff679a88e29fe`, em `docs/cia-dfd.md`, com fonte Mermaid em `docs/dfd-atual.mmd`. O DFD mostra memória, JSON e HTML reais; JWT, laboratório M2M e banco são lacunas/fases futuras.
- **Alternativas:** usar outras edições ou ATT&CK para técnicas de ataque. Uma mudança futura exigirá justificativa e remapeamento; não altera os requisitos do Assessment.
- **Consequências:** IDs AT/P/F/TB ficam estáveis para o STRIDE. TB-02 é limite lógico de divulgação, sem isolamento de processo; lock não é autorização nem garantia de conflito de agenda. Notas e dados clínicos permanecem sensíveis em memória e nos fluxos internos.
- **Verificação:** inspeção de rotas, schemas, armazenamento, templates e percursos JSON/HTML; reaproveitamento das evidências reais Ex. 1/2. Não executar testes artificiais para tabelas nem alegar controles dos incrementos futuros. Fontes primárias e limitações constam no relatório.

---

### DEC-01: Organização e Layout Modular da Aplicação
- **Contexto:** O projeto exige modularização desde o início para suportar a evolução incremental dos 13 exercícios, prevenindo acoplamento em arquivo único (`main.py`).
- **Opções Analisadas:**
  1. Todos os endpoints e modelos concentrados em `main.py` (Rejeitado: viola os requisitos do Assessment e boas práticas).
  2. Pacote `app/` estruturado com subpastas `routes/`, `models/`, `database/`, e futura expansão para `auth/`, `middleware/` e `templates/` (Adotado).
- **Consequência:** Separação limpa de preocupações (SRP): rotas cuidam de HTTP, models de validação de dados e database de persistência/armazenamento.

---

### DEC-02: Contrato REST e Representação de Consultas
- **Contexto:** Definir o contrato RESTful das operações de consultas médicas (Exercício 1).
- **Decisão:**
  - `POST /consultas`: Criação de nova consulta (retorna 201 Created com a consulta criada).
  - `GET /consultas`: Listagem de consultas (retorna 200 OK com lista de consultas).
  - `GET /consultas/{id}`: Obtenção de consulta específica por ID (retorna 200 OK ou 404 Not Found).
  - `PATCH /consultas/{id}`: Atualização parcial de campos como status ou data/hora (retorna 200 OK ou 404 Not Found).
  - `DELETE /consultas/{id}`: Cancelamento/remoção da consulta (retorna 204 No Content ou 404 Not Found).
  - Modelo de dados de consulta inclui: `id`, `paciente_id`, `profissional_id`, `data_hora`, `status`, `motivo` e `observacoes_internas` (campo confidencial/auditoria).
- **Consequência:** Semântica REST documentada, permitindo testes imediatos e evolução para response models seguros no Exercício 2. `DELETE` remove fisicamente o registro nesta etapa; cancelamento como mudança de estado permanece uma decisão de negócio a definir.
- **Pendências:** duração das consultas, conflito de horários, estados permitidos e comportamento futuro de cancelamento. O fuso provisório adotado no Exercício 2 está na DEC-14. O `PATCH` rejeita `null` em campos obrigatórios, mas não fixa ainda um catálogo de estados.

---

### DEC-13: Contratos de saída e minimização no Exercício 2

- **Contexto:** o modelo interno `Consulta` contém `observacoes_internas`, `criado_em` e `atualizado_em`; devolver essa entidade inteira exporia notas confidenciais e metadados de auditoria. A evidência histórica do Exercício 1 mostra esse estado anterior. A presença de qualquer `response_model` não basta: o modelo anterior declarava também os campos internos.
- **Decisão:** criar `ConsultaResponse`, derivado apenas de `ConsultaBase`, com `id` e `status` obrigatórios; aplicar nas respostas POST, GET unitário/listagem e PATCH. DELETE continua sem corpo (204). Os seis campos autorizados são `id`, `paciente_id`, `profissional_id`, `data_hora`, `motivo` e `status`. O motivo permanece no contrato clínico JSON; sua autorização será implementada no Exercício 6.
- **Alternativa rejeitada:** repetir exclusões por rota ou retornar a entidade inteira, pois novos campos internos poderiam vazar e as listas de exclusão poderiam divergir. A allowlist de saída é um contrato próprio e continua válida após a migração SQLModel.
- **Agenda:** o template recebe uma projeção somente com IDs de consulta/paciente/profissional, horário local e status, suficiente para a demonstração inicial da recepção. Não recebe motivo, observações, datas de auditoria, email ou prontuário. Exibir nomes e definir o mínimo operacional definitivo são decisões futuras de produto; os IDs não devem ser tratados como dados anônimos.
- **Segurança:** `agenda.html` estende `base.html`; o Environment usa `select_autoescape` explicitamente para HTML/XML. Texto variável fica em nós de texto ou atributos HTML escapados; não há `safe`, JavaScript dinâmico ou CSS com conteúdo do usuário. Escape não substitui autorização.
- **Verificação:** testes HTTP comparam o conjunto exato de campos em quatro respostas e confirmam preservação dos dados internos. Dois ataques didáticos via PATCH de status comprovam armazenamento do texto e sua renderização como texto, sem criar tags `script`/`img`. O catálogo de status ainda está pendente; o campo textual existente permite exercitar a defesa de saída sem reintroduzir vulnerabilidade.
- **Fontes técnicas:** [FastAPI: response models e filtragem](https://fastapi.tiangolo.com/tutorial/response-model/) e [Jinja2: autoescaping](https://jinja.palletsprojects.com/en/stable/api/#autoescaping). A proteção efetiva foi verificada na aplicação instalada, não inferida apenas da documentação.

---

### DEC-14: Dia e fuso da agenda inicial

- **Recomendação de engenharia adotada provisoriamente:** `America/Sao_Paulo` é o fuso único desta demonstração; o Assessment não define o fuso nem múltiplas clínicas com fusos diferentes. Confirmar esta convenção antes da disponibilidade M2M e persistência. Não é requisito acadêmico adicional.
- **Decisão:** `GET /agenda?dia=AAAA-MM-DD`; sem `dia`, usar o dia atual nesse fuso, sem depender do fuso do servidor. Horários ingênuos existentes são interpretados como locais; horários com offset são convertidos. Filtrar pela data local e ordenar pelo instante convertido.
- **Alternativas:** exigir offset em todos os horários e armazenar UTC na persistência; ou configurar fuso por clínica, se o domínio efetivamente exigir. Não introduzir esse escopo agora.
- **Implementação:** regra temporal compartilhada em `app/database/consultas.py`; a rota coordena HTTP e projeção, o template só apresenta. `tzdata` provê fallback da base IANA em sistemas que não a tenham; templates são incluídos como package data e localizados a partir de `__file__`.
- **Verificação:** data inválida rejeitada com 422, agenda vazia explícita, dia atual com relógio controlado e instante UTC no dia anterior local.
- **Limites:** não há validação de horários locais ambíguos/inexistentes, duração, conflito ou catálogo de status. Esses pontos precisam de decisão antes de prometer garantias de disponibilidade ou consistência.

---

### DEC-03: Estrutura de Vínculo entre Paciente, Profissional e Consulta
- **Contexto:** A regra de negócio RN-01 exige que um profissional só crie e gerencie consultas dos seus próprios pacientes.
- **Decisão:**
  - Manter referências explícitas (`paciente_id`, `profissional_id`) na consulta.
  - Para a fase inicial em memória (Ex. 1), prover seeds fictícios de pacientes e profissionais para exemplificar as referências. A API ainda não valida a existência desses IDs nem o vínculo entre eles.
- **Consequência:** As referências explícitas facilitam a introdução da verificação de vínculo e ownership no Exercício 6. Os dados fictícios atuais não comprovam integridade referencial.

---

### DEC-04: Persistência Inicial e Banco Relacional Final
- **Contexto:** O Exercício 1 exige módulos `database/` e um recurso funcional; o armazenamento em memória é uma escolha temporária de engenharia. O Exercício 11 exige migração para SQLModel e banco relacional.
- **Decisão:**
  - Implementar inicialmente um repositório em memória em `app/database/memoria.py` e funções de acesso em `app/database/consultas.py`.
  - Isolar as funções de acesso para que as rotas em `app/routes/consultas.py` dependam de contratos de função (`criar_consulta`, `obter_consulta`, etc.), minimizando o impacto na migração do Ex. 11.
- **Decisão a definir:** Motor relacional final (por exemplo, SQLite ou PostgreSQL), estratégia de migração e garantias de concorrência. Não atribuir garantias iguais a motores diferentes sem verificar.
- **Consequência:** Mantém a fundação funcional sem repositórios genéricos. Antes do Exercício 11, esta decisão será complementada com o banco escolhido, a estratégia de migração e as garantias de concorrência verificadas.

---

### DEC-06: Gerenciamento de Dependências e Configuração
- **Contexto:** Necessidade de ambiente reproduzível e isolado.
- **Decisão:**
  - Uso de ambiente virtual `.venv` com Python 3.14.
  - `pyproject.toml` como manifesto declarativo de dependências do projeto e configuração do pytest.
  - `pydantic-settings` e `.env.example` previstos para isolamento de configurações futuras.
- **Consequência:** Ambiente isolado e dependências declaradas. O `pyproject.toml` usa versões mínimas, sem lockfile; reprodução exata das versões ainda não está garantida. As versões observadas na execução inicial constam em `evidencias/ex01/ambiente_versao.txt`.

## DEC-18 — Identidade, sessão e autorização do Ex. 6

Contexto: três papéis, gestão de pacientes próprios e MFA administrativo. Matriz e cookie de agenda foram aprovados pelo responsável pelo projeto. Escolha: RBAC por família de operação mais vínculo confiável e ownership; diagnóstico admin sem clínica; bcrypt custo 12; PyJWT HS256/TTL 15 minutos; BaseSettings sem chave padrão; cadastro fictício local ignorado; desafio único/300s/cinco erros; fator estático local somente para simulação. Cookie HttpOnly/SameSite Strict/Secure com path `/agenda`, aceito apenas na leitura HTML; sessão exige bearer.

Alternativas: RBAC isolado não resolve BOLA; motor ABAC genérico seria prematuro; bearer exclusivo em HTML exigiria cliente HTTP controlado; armazenar token em URL exporia credencial. Escolhas detalhadas, claims, limites e comandos em [autenticacao-autorizacao.md](autenticacao-autorizacao.md).

Consequências: autorização é centralizada e preserva os controles JSON/HTML. Cadastro e desafio não são solução relacional/multiworker; não há MFA real, refresh ou revogação individual. Mudanças de arquivo exigem restart. TTL curto reduz janela, sem eliminar roubo de sessão. Rate limiting, TLS/headers, M2M e migração SQLModel continuam pendentes. Não há autorização para deploy.

## DEC-19 — Client Credentials e disponibilidade do parceiro

Contexto: laboratório atua em nome próprio, limitado a horários livres. Escolha técnica: Client Credentials separado do login humano, Basic com hash bcrypt local, scope único `disponibilidade:ler`, subject `client:<id>`, finalidade `m2m_access`, audiência `clinic-laboratory` e TTL de cinco minutos. Cliente não vira profissional nem administrador. Sem credencial configurada, M2M é negado sem interromper a aplicação humana.

Regra aprovada pelo responsável: consultas de demonstração de 30 minutos, dias úteis 08h–18h, America/Sao_Paulo; cancelada libera e demais estados bloqueiam; resposta por profissional com intervalos livres. A verificação considera sobreposição e offset. Não se trata de exigência adicional da disciplina nem de reserva atômica.

Alternativas: Authorization Code representa delegação de usuário, ausente nesse cenário; senha humana compartilhada mistura privilégios; credenciais no corpo são desnecessárias quando Basic atende ao cliente confidencial. Consequências: hash/segredo ficam fora da entrega; configurar e reiniciar para ativar; tokens humanos/M2M permanecem segregados; regras de reserva, concorrência, feriados e duração variável permanecem pendentes. [Contrato e limites](integracao-m2m.md) e evidências Ex. 7 registram a decisão.

## DEC-20 — Revisão OWASP e cenário de paciente do Ex. 8

Contexto: ownership e auto-escape já existem, mas o cenário acadêmico exige BOLA de paciente autenticado e não há esse papel/prontuário na aplicação. Decisão aprovada pelo responsável: revisar código histórico real e atual; demonstrar separadamente dois pacientes fictícios em experimento local, sem portal ou rota vulnerável na aplicação. O aceite acadêmico desse enquadramento permanece pendente.

Fixado OWASP Top 10:2021 para comparar categorias distintas, com API1:2023 identificado como referencial separado de BOLA. Encontrados A01 histórico, A05 e A07 atuais, com localizações e observações reproduzidas. SQL Injection e XSS não foram inventados: memória não executa SQL e a agenda escapa o payload. Campos extras ignorados são lacuna de contrato, sem elevação de privilégio demonstrada.

Consequências: fontes de cada baseline têm SHA-256 e snapshots literais; nenhuma correção ou regressão vulnerável entrou em app/. Atributo Git de whitespace é limitado aos snapshots para conservar inclusive espaços da fonte histórica, não aos arquivos de aplicação. Ex. 9 reutiliza payloads e esclarece SQL/XSS; Ex. 10 trata headers/throttling; Ex. 12 prioriza findings com CVSS/negócio. [Relatório da revisão](vulnerabilidades.md) registra evidência, estado e limite acadêmico.

## DEC-21 — Contratos estritos e middleware JWT do Ex. 9

Contexto: consultas e formulário M2M ignoravam extras, status era texto livre e os validadores JWT eram chamados por dependências. Escolha: middleware ASGI puro estabelece identidade por segmento protegido e dependências consomem esse principal; políticas existentes continuam verificando papel, vínculo e objeto antes de leitura/mutação. Não criar ownership baseado só no caminho nem duplicar decode nas dependências.

Regras aprovadas: status `agendada`, `cancelada`, `realizada`; username ASCII com regex, sem regex restritiva de texto clínico. POST/PATCH JSON passam a rejeitar extras; omissão de campo no PATCH conserva semântica parcial e nulo só apaga notas. Cookie da agenda mantém escopo e não contorna Authorization inválido.

Endpoint adicional aprovado: formulário `/auth/m2m/token`, não citado como finding de extras no Ex. 8. Modelo `M2MTokenInput` permite somente grant_type/scope; preserva Basic, protocolo de grant e distinção de scope omitido/vazio. Baseline real reproduzido a partir dos snapshots SHA-256 prova que o extra antes era ignorado. Inventário já continha a rota; interpretação literal de nunca citada permanece pendente.

Experimento aprovado: SQLite isolado e fictício para mostrar concatenação vulnerável e parametrização corrigida, preservando SQLModel para Ex. 11. BOLA com paciente permanece didático isolado. Alternativa de antecipar banco relacional foi recusada nesta etapa; enfraquecer rotas reais para criar ANTES foi descartado. Auto-escape existente é preservado, não inventado como correção nova de XSS explorado.

Consequências: novos recursos protegidos devem integrar middleware e política; overrides de Depends não alteram automaticamente middleware. Dado legado exige defesa de saída mesmo com allowlist. R14–R16 e aceite acadêmico dos experimentos permanecem com lacunas registradas; headers/throttling abertos para Ex. 10. [Análise e comparações](correcoes-entrada-saida.md) explicam limites.

## DEC-22 — Hardening local e cotas de requisição

Contexto: ausência de headers e sequência de 20 erros de senha sem throttling foram demonstradas no Ex. 8. Escolha: origem de demonstração configurável `http://localhost:5173`, sem wildcard ou credenciais CORS, DENY/nosniff nas respostas e HSTS de um ano somente HTTPS. Não pressupor domínio, certificado, proxy confiável ou frontend implementados.

Limites escolhidos para o exercício: cinco requisições/minuto por IP compartilhadas entre login humano, Client Credentials e MFA; 60/minuto nas demais rotas; preflight atendido antes da autenticação/cota. Janela móvel, relógio monotônico, lock, memória e estado por arranque. Resposta 429 com Retry-After não prolonga a janela. O orçamento MFA por desafio permanece um controle distinto.

Alternativas: serviço externo de contagem não é necessário para demonstração em um processo; contador por username sozinho permitiria bloquear conta de terceiro. Sem infraestrutura de proxy definida, usar endereço da conexão e `--no-proxy-headers` no Uvicorn local. Não adicionar Redis, frontend, TLS fictício ou requisitos numéricos atribuídos à disciplina.

Consequências: NAT compartilha cotas; múltiplos workers/reinícios/ataque distribuído não são cobertos. HTTPS do TestClient demonstra headers, não handshake TLS. VUL-002/003 têm controles verificados no escopo local; riscos de implantação seguem abertos. [Hardening](hardening.md) e evidências Ex. 10 registram testes e parâmetros.
