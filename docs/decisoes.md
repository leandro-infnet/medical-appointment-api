# Registro de Decisões Técnicas (ADR / Decisões de Projeto)

Este documento registra as decisões arquiteturais e técnicas de maior relevância para o desenvolvimento da API de agendamento de consultas.

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
- **Pendências:** fuso e duração das consultas, conflito de horários, estados permitidos e comportamento futuro de cancelamento. O `PATCH` rejeita `null` em campos obrigatórios, mas não fixa ainda um catálogo de estados.

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
- **Consequência:** Mantém a fundação funcional sem repositórios genéricos. A escolha do banco final será registrada antes do Exercício 11, conforme DEC-04 no guia.

---

### DEC-06: Gerenciamento de Dependências e Configuração
- **Contexto:** Necessidade de ambiente reproduzível e isolado.
- **Decisão:**
  - Uso de ambiente virtual `.venv` com Python 3.14.
  - `pyproject.toml` como manifesto declarativo de dependências do projeto e configuração do pytest.
  - `pydantic-settings` e `.env.example` previstos para isolamento de configurações futuras.
- **Consequência:** Ambiente isolado e dependências declaradas. O `pyproject.toml` usa versões mínimas, sem lockfile; reprodução exata das versões ainda não está garantida. As versões observadas na execução inicial constam em `evidencias/ex01/ambiente_versao.txt`.
