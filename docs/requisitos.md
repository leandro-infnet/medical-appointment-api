# Requisitos e Escopo — API de Agendamento de Consultas

## 1. Visão Geral e Contexto

O produto é uma API REST desenvolvida em FastAPI para digitalização do agendamento de consultas médicas em uma rede de clínicas. Lida com dados de pacientes e profissionais de saúde, que exigem controles de segurança. Este documento registra requisitos e decisões de projeto; não comprova conformidade com a LGPD. No Exercício 1, as rotas ainda não têm autenticação nem autorização.

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
4. **Campos Internos de Auditoria:** `observacoes_internas`, `criado_em` e `atualizado_em` existem no modelo inicial. Outros campos, como IP de origem e versão de registro, são apenas possibilidades futuras. Os campos internos deverão ser excluídos das respostas JSON públicas no Exercício 2. Hoje ainda são expostos.
5. **Dados de Disponibilidade:** Apenas intervalos livres de agenda (sem expor paciente ou motivo).

---

## 4. Requisitos Funcionais

Os itens desta seção representam o **alvo do Assessment completo**; no Exercício 1, apenas RF-01 está implementado. A aplicação ainda não oferece os controles das etapas seguintes.

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
