# Requisitos e Escopo — API de Agendamento de Consultas

## 1. Visão Geral e Contexto

O produto é uma API REST desenvolvida em FastAPI para digitalização do agendamento de consultas médicas em uma rede de clínicas. Lida com dados de pacientes e profissionais de saúde, que exigem controles de segurança. Este documento registra requisitos e decisões de projeto; não comprova conformidade com a LGPD. Até o Exercício 2, as rotas ainda não têm autenticação nem autorização.

### Consumidores do Sistema
1. **Frontend JSON:** Aplicação consumidora das rotas REST da API.
2. **Página HTML da Recepção:** Interface interna (Jinja2) para consulta da agenda diária pelos recepcionistas.
3. **Laboratório Parceiro M2M:** Integração máquina-a-máquina restrita à consulta de horários disponíveis.

### Atores Internos do Domínio
- **Recepcionista:** Consulta agenda diária com informações mínimas necessárias para recepção.
- **Profissional de Saúde:** Cria, visualiza e gerencia consultas médicas dos seus próprios pacientes.
- **Administrador:** Possui acesso a pelo menos uma rota administrativa restrita, com MFA simulado; as operações administrativas específicas ainda serão definidas.

---

## 2. Matriz Inicial de Atores x Operações x Recursos

Esta matriz propõe restrições para as etapas futuras. **Permitido** significa comportamento a implementar, não proteção já existente. O Assessment não define todas as permissões: decisões ausentes precisam ser registradas antes da implementação. Em particular, o paciente autenticado é citado no cenário BOLA do Exercício 8, mas não faz parte dos três papéis internos definidos inicialmente.

| Ator | Criar Consulta | Visualizar Próprias Consultas | Visualizar Consultas Alheias | Agenda Diária HTML | Rota Administrativa | Consultar Disponibilidade (M2M) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Profissional** | Permitido (seus pacientes) | A definir: alcance da leitura | Negado conforme ownership | A definir | Negado sem papel administrativo | A definir |
| **Recepcionista** | Negado | Negado | Negado | Permitido (leitura do dia) | Negado | Negado |
| **Administrador** | Negado somente por ser administrador | A definir | A definir | A definir | Permitido (com MFA) | A definir |
| **Laboratório M2M**| Negado | Negado | Negado | Negado | Negado | Permitido (escopo restrito) |
| **Paciente Autenticado** | A definir | A definir: acesso ao próprio prontuário | Negado (Cenário BOLA Ex. 8) | A definir | Negado | A definir |
| **Anônimo** | Negado | Negado | Negado | Negado | Negado | Negado |

---

## 3. Classificação dos Dados

1. **Dados Pessoais:** Nome do paciente, identificador, contato.
2. **Dados Sensíveis de Saúde:** Consultas, especialidade/motivo, histórico/prontuário clínico.
3. **Credenciais e Segredos:** Senhas com hash bcrypt, chaves de assinatura JWT, tokens M2M, códigos MFA.
4. **Campos Internos de Auditoria:** `observacoes_internas`, `criado_em` e `atualizado_em` existem no modelo interno, mas foram excluídos das respostas JSON pelo `ConsultaResponse` no Exercício 2. Outros campos, como IP de origem e versão de registro, são apenas possibilidades futuras. A agenda também exclui motivo clínico e notas internas de seu contexto.
5. **Dados de Disponibilidade:** Apenas intervalos livres de agenda (sem expor paciente ou motivo).

---

## 4. Requisitos Funcionais

Os itens desta seção representam o **alvo do Assessment completo**; RF-01 e RF-02 estão implementados e verificados. A aplicação ainda não oferece os controles das etapas seguintes.

- **RF-01:** Prover CRUD RESTful completo de consultas médicas (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`) com validação explícita de schemas.
- **RF-02:** Controlar exposição de dados via `response_model` no JSON e renderizar agenda diária HTML com Jinja2 com auto-escape.
- **RF-03:** Prover autenticação humana via `OAuth2PasswordBearer`, JWT com expiração e simulação de MFA administrativo.
- **RF-04:** Prover autorização baseada em papéis e controle de acesso em nível de objeto (ownership).
- **RF-05:** Prover autenticação M2M (OAuth2 Client Credentials) com escopos restritos para o laboratório parceiro.
- **RF-06:** Persistir dados relacionais com SQLModel, queries parametrizadas e injeção de dependência de sessão.

---

## 5. Requisitos Não Funcionais e Segurança

Estes controles serão implementados progressivamente. A lista não afirma que já estão ativos na fundação do Exercício 1.

- **RNF-01 (Arquitetura):** Modularização estrita em `routes/`, `models/`, `database/`, `auth/` e `middleware/`.
- **RNF-02 (Defesa em Profundidade):** Validação estrita de entrada (`extra='forbid'`, allowlists, regex) e auto-escape contra XSS.
- **RNF-03 (Hardening de Rede):** CORS com origens explícitas, cabeçalhos de segurança (HSTS, X-Frame-Options, X-Content-Type-Options) e rate limiting em endpoints sensíveis (login).
- **RNF-04 (Configuração Segura):** Segredos e credenciais via `pydantic-settings` (`BaseSettings`) lendo `.env`, com `.env.example` versionado.
- **RNF-05 (Pipeline e Auditoria):** Pipeline DevSecOps com security gate automatizado e auditoria passiva via OWASP ZAP.

## 6. Verificação do Exercício 2

| Cenário | Comportamento esperado | Verificação |
| --- | --- | --- |
| Entidade contém notas e datas internas | JSON contém somente os seis campos contratados, sem apagar dados internos | `test_respostas_excluem_campos_internos_sem_apagar_armazenamento` |
| Agenda contém consultas de dias/horários distintos | Só o dia solicitado, em ordem local; contexto mínimo | `test_agenda_filtra_dia_ordena_e_minimiza_contexto` |
| Instante UTC pertence ao dia anterior local | Conversão precede filtro de dia | `test_agenda_converte_instante_utc_antes_de_filtrar_dia` |
| Status contém script ou imagem com handler | Conteúdo armazenado é exibido como texto, sem tags executáveis | `test_agenda_escapa_texto_malicioso_armazenado` |
| Dia vazio, omitido ou inválido | Mensagem de vazio, dia atual local ou 422, respectivamente | Demais testes de agenda |

Referências e resultados: [decisões DEC-13/14](decisoes.md), [rastreabilidade](rastreabilidade.md) e [evidências](../evidencias/ex02/README.md). CIA/DFD, misuse cases/STRIDE e partições de segurança estão documentados nos Exercícios 3, 4 e 5; os controles futuros continuam planejados.

## 7. Fundamentos de segurança — Exercício 3

Análise CIA e DFD atual documentados em [cia-dfd.md](cia-dfd.md). A revisão distingue controles implementados, lacunas e arquitetura futura; não introduz novos controles executáveis.

| Requisito documental | Entrega | Rubrica |
| --- | --- | --- |
| REQ-03.1: CIA da aplicação construída | Cenários CIA-01–08 com ativos, impactos, controles e limites de verificação | R05 |
| REQ-03.2: OWASP, NIST SSDF e MITRE associados a controles reais | Mapeamento com edição, item, código, teste/evidência e limite; DEC-15 | R05 |
| REQ-03.3: DFD, fluxos sensíveis e trust boundaries | E-01/02, P-01–03, D-01, F-01–10, TB-01 real e TB-02 lógico; futuras TB-03/04 explicitamente separadas | R06 |

LAC-01–06 registram autorização ausente, validação parcial, controle de abuso, memória volátil e demais pontos a desenvolver. Não são Threat IDs nem findings de scanner. Sua ligação ao STRIDE do Exercício 4 está no threat model. A aplicação permanece no estado funcional do Exercício 2.

## 8. Threat modeling — Exercício 4

| Requisito | Entrega / verificação documental | Rubrica |
| --- | --- | --- |
| REQ-04.1: misuse cases relevantes | MU-001–012: ator, precondição, tentativa, resultado proibido e ligação a fluxo/controle/teste; cenários futuros identificados | R07 |
| REQ-04.2: STRIDE em pelo menos três componentes | P-01/P-02/P-03, com seis categorias examinadas em cada um e 18 linhas de análise | R08 |
| REQ-04.3: threat model consolidado | AT/SUP/MU/TM/CTRL/TEST rastreáveis; 16 ameaças, estados de mitigação e risco residual; snapshot inicial 1.0 | R08 |

Entrega em [threat-model.md](threat-model.md), decisão DEC-16 e [evidências Ex. 4](../evidencias/ex04/README.md). Novos testes são planejados para seus incrementos; o documento não comprova exploração, correção executada ou CVSS. As permissões de paciente autenticado, vínculo paciente/profissional e regras de disponibilidade permanecem decisões pendentes.

## 9. Arquitetura de segurança — Exercício 5

| Requisito | Entrega / verificação documental | Rubrica |
| --- | --- | --- |
| REQ-05.1: partições do sistema | Componentes atuais/futuros, responsabilidade, localização, dados e controles; composição modular no mesmo processo | R09 |
| REQ-05.2: fluxo entre componentes | Pares F-01–10 do DFD na visão de partições, dados sensíveis e TB atuais/lógicas/futuras | R09 |
| REQ-05.3: vetores nos três eixos | VD-01–04 (design), VI-01–04 (implementação), VF-01–04 (infraestrutura), ligados a TM/CTRL/TEST | R09 |

Entrega em [arquitetura-seguranca.md](arquitetura-seguranca.md), fonte [particoes-seguranca.mmd](particoes-seguranca.mmd), DEC-17 e [evidências Ex. 5](../evidencias/ex05/README.md). A arquitetura identifica decisões prévias ao Ex. 6, sem implementar JWT, sessão HTML, middleware ou SQLModel.
