# Requisitos e escopo

API de agendamento para clínicas, com frontend consumidor JSON, agenda HTML da recepção e laboratório parceiro M2M. A aplicação usa dados fictícios; prontuário e portal de paciente não fazem parte do produto.

## Permissões

| Ator | Consultas JSON | Agenda HTML | Administração | Disponibilidade M2M |
| --- | --- | --- | --- | --- |
| Profissional | CRUD dos pacientes vinculados ao próprio profissional | Não | Não | Não |
| Recepção | Não | Leitura mínima do dia | Não | Não |
| Administrador | Não | Não | Diagnóstico após MFA simulado | Não |
| Laboratório | Não | Não | Não | Leitura com scope próprio |
| Anônimo | Não | Não | Não | Não |

O frontend usa a identidade humana; não recebe permissão própria. Paciente autenticado aparece apenas no experimento BOLA do Ex. 8. O aceite acadêmico desse recorte permanece pendente.

## Dados

| Classe | Campos / tratamento |
| --- | --- |
| Identificação e vínculo | IDs de paciente/profissional, horário e status; vinculam pessoas ao atendimento |
| Saúde | `motivo`, `observacoes_internas`; acesso profissional restrito |
| Dados internos | Notas, `criado_em`, `atualizado_em`; ausentes da saída JSON/agenda |
| Segredos | Senhas, hashes, chave JWT, tokens e MFA; fora dos logs, Git e ZIP |
| Disponibilidade | Profissional, dia, fuso e intervalos livres; sem paciente/motivo |

IDs numéricos não tornam dados anônimos. Nome, contato e prontuário não são campos do contrato de consultas.

## Requisitos funcionais

| ID | Requisito | Implementação |
| --- | --- | --- |
| RF-01 | CRUD RESTful validado por APIRouter | `app/routes/consultas.py` |
| RF-02 | Response models e agenda diária Jinja2 com herança/escape | `models/consultas.py`, `routes/agenda.py`, `templates/` |
| RF-03 | OAuth2PasswordBearer, bcrypt, JWT expirável e MFA simulado | `app/auth/`, `routes/auth.py` |
| RF-04 | Papéis e ownership por vínculo confiável | `auth/policies.py`, `database/identidades.py` |
| RF-05 | OAuth Client Credentials, scopes/claims M2M distintos | `auth/m2m.py`, `routes/disponibilidade.py` |
| RF-06 | SQLModel relacional, parâmetros e sessão injetada | `database/session.py`, `database/consultas.py`, `models/tabelas.py` |

## Requisitos não funcionais

| ID | Requisito | Verificação |
| --- | --- | --- |
| RNF-01 | Módulos HTTP, modelos, dados e autenticação separados | Revisão da [arquitetura](arquitetura-seguranca.md) |
| RNF-02 | Validação explícita, extra forbid, allowlist/regex e escape | `test_seguranca_entrada_saida.py`, `test_respostas_templates.py` |
| RNF-03 | CORS explícito, headers e rate limiting diferenciado | `test_hardening.py`; TLS real permanece pendente |
| RNF-04 | BaseSettings/.env, sem credenciais reais na entrega | `test_autorizacao.py`, `test_persistencia.py`; `.env.example` |
| RNF-05 | Pipeline, gate e auditoria passiva ZAP | `test_security_gate.py`, workflow e evidências Ex. 12/13 |

## Decisões de domínio

Escolhas de projeto, além dos controles exigidos: vínculos fictícios `(1,1)`, `(2,1)`, `(2,2)`; fuso `America/Sao_Paulo`; duração de 30 minutos; status agendada/cancelada/realizada; cancelada libera horário; sobreposição do mesmo profissional gera 409. Disponibilidade considera dias úteis 08h–18h, mas o CRUD não impõe esse expediente. DELETE remove o registro; cancelamento usa PATCH de status.

A [matriz de rastreabilidade](rastreabilidade.md) relaciona todos os exercícios à rubrica. [Decisões](decisoes.md) registra alternativas e limites; [capstone](relatorio-capstone.md) consolida findings e decisão de liberação.
