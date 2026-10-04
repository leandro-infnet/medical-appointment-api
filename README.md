# API de Agendamento de Consultas Médicas

API REST desenvolvida com FastAPI para agendamento de consultas médicas em uma rede de clínicas. Os Exercícios 1 e 2 entregam o CRUD modular, respostas JSON com campos controlados e agenda diária HTML com herança Jinja2 e escape de saída. O Exercício 6 adiciona bcrypt, JWT, MFA administrativo simulado e autorização por papel/vínculo/recurso. Persistência relacional permanece futura; execute localmente com dados fictícios.

## Requisitos

- Python 3.11+ (desenvolvido e testado com Python 3.14)
- Ambiente virtual isolado (`.venv`)

## Instalação

1. Clone o repositório e navegue até a pasta do projeto:
```bash
cd /caminho/do/projeto
```

2. Crie e ative o ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -e ".[dev]"
```

O manifesto declara versões mínimas. As versões usadas na demonstração do Exercício 1 estão em `evidencias/ex01/ambiente_versao.txt`; ainda não há lockfile.

As versões do Exercício 2 constam em `evidencias/ex02/ambiente_versao.txt`. `tzdata` fornece a base de fusos IANA quando ela não existe no sistema operacional.

## Configurar identidade antes de executar

Copie `.env.example` para `.env`, defina a chave JWT aleatória e o código MFA fictício e execute `.venv/bin/python -m app.auth.provision`. Para cookie da agenda em HTTP local, configure explicitamente `AGENDA_COOKIE_SECURE=false`; o padrão exige HTTPS. Sem configuração/cadastro válido, o startup falha. Senhas são solicitadas sem eco e ficam somente como bcrypt no cadastro ignorado `.local/usuarios.json`.

Passos completos, contas, login, MFA e navegação estão em [docs/autenticacao-autorizacao.md](docs/autenticacao-autorizacao.md). Nunca incluir `.env`, cadastro, credenciais reais ou tokens no repositório/ZIP.

## Execução do Servidor

Para iniciar a aplicação com recarregamento automático (modo de desenvolvimento):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

A documentação interativa OpenAPI (Swagger UI) estará disponível em:
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Consultas e agenda diária

As respostas de criação, listagem, leitura e atualização contêm somente `id`, `paciente_id`, `profissional_id`, `data_hora`, `motivo` e `status`. `observacoes_internas`, `criado_em` e `atualizado_em` permanecem no armazenamento, mas não saem no JSON.

Após login como recepção e criação da sessão em `POST /auth/agenda-session`, abra [http://127.0.0.1:8000/agenda](http://127.0.0.1:8000/agenda) para o dia atual da clínica, ou `/agenda?dia=2026-10-03` para uma data explícita. A página apresenta horário, IDs de consulta/paciente/profissional e status; não recebe motivo clínico nem notas internas. Data inválida resulta em HTTP 422; dia vazio tem mensagem própria.

**Decisão de domínio aprovada para a demonstração (DEC-19):** `America/Sao_Paulo` como fuso da clínica. Horários sem offset são interpretados nesse fuso; horários com offset são convertidos antes de filtrar o dia. Esta convenção não foi imposta pela disciplina; foi aprovada no incremento de disponibilidade. A escolha é explicada em [docs/decisoes.md](docs/decisoes.md).

A agenda é restrita à recepção autenticada. CRUD JSON exige bearer profissional e vínculo confiável. Escape HTML evita interpretação das entradas como marcação; não substitui controle de acesso.

## Execução dos Testes Automatizados

Para rodar a suíte de testes com pytest:

```bash
.venv/bin/python -m pytest tests/ -v
```

## Estrutura de Módulos

A aplicação segue a organização modular de responsabilidades separadas:
- `app/main.py`: Ponto de entrada e composição da aplicação FastAPI.
- `app/routes/`: Roteadores HTTP (`APIRouter`) tratando requisições, status e parâmetros.
- `app/models/`: Schemas Pydantic para validação de entrada e saída.
- `app/database/`: Camada de gerenciamento de dados e persistência.
- `app/templates/`: Layout HTML compartilhado (`base.html`) e agenda que o estende, com auto-escape explícito.
- `docs/`: Documentação técnica de arquitetura, requisitos e decisões.
- `evidencias/`: Evidências de execução de cada exercício do Assessment.
- `tests/`: Suíte de testes automatizados com pytest.

## Evidências do Exercício 2

[evidencias/ex02/README.md](evidencias/ex02/README.md) relaciona requisitos, testes, respostas HTTP, HTML e screenshot real. O script `evidencias/ex02/reproduzir.py` é histórico e deve ser executado no baseline do Ex. 2, sem autenticação. Não executá-lo na versão atual nem sobrescrever evidências antigas. A reprodução autenticada está em `evidencias/ex06/reproduzir.py`.

## Análise de segurança — Exercício 3

[docs/cia-dfd.md](docs/cia-dfd.md) analisa confidencialidade, integridade e disponibilidade, mapeia OWASP/NIST SSDF/MITRE a controles existentes e apresenta o DFD do incremento atual. A fonte editável está em [docs/dfd-atual.mmd](docs/dfd-atual.mmd); exportação e revisão estão em [evidencias/ex03/README.md](evidencias/ex03/README.md).

A exportação do Ex. 3 preserva JSON, HTML e memória daquele baseline. A fonte atual inclui identidade/políticas e sessão do Ex. 6; M2M e persistência relacional permanecem futuras. IDs de ativos, processos, fluxos e fronteiras serão reutilizados no STRIDE do Exercício 4. O mapeamento e seus limites constam em [docs/rastreabilidade.md](docs/rastreabilidade.md).

## Modelagem de ameaças — Exercício 4

[docs/threat-model.md](docs/threat-model.md) consolida 12 misuse cases, as seis categorias STRIDE nos três processos reais do DFD, 16 ameaças e sua relação com ativos, superfícies, controles, testes e riscos residuais. A versão inicial registra JWT, M2M e SQL como futuros naquele baseline. A extensão 1.2 registra autenticação efetiva e os riscos residuais do Ex. 6; a memória continua temporária.

[evidencias/ex04/README.md](evidencias/ex04/README.md) registra a revisão e preserva a versão inicial para comparar com os incrementos seguintes. Os testes existentes de filtragem JSON e escape HTML estão vinculados a TM-004/TM-005 como evidências históricas. As mitigações futuras e os respectivos testes não estão marcados como executados.

## Arquitetura de segurança — Exercício 5

[docs/arquitetura-seguranca.md](docs/arquitetura-seguranca.md) descreve partições, fluxos, fronteiras e doze vetores nos eixos design, implementação e infraestrutura. Localiza CTRL-01–11 e registra decisões de identidade, autorização por recurso, autenticação HTML, middleware, rede e persistência que orientarão os incrementos seguintes.

Nesse baseline histórico, o código permanecia no estado funcional dos Exercícios 1/2; os componentes futuros estão identificados como planejados. Fonte Mermaid, SVG, screenshot e revisão estão em [evidencias/ex05/README.md](evidencias/ex05/README.md), com rastreabilidade R09 em [docs/rastreabilidade.md](docs/rastreabilidade.md).

## Autenticação e autorização — Exercício 6

[docs/autenticacao-autorizacao.md](docs/autenticacao-autorizacao.md) descreve a matriz aprovada, RBAC com ownership/atributos, contrato JWT, MFA simulado e cookie exclusivo da agenda. [evidencias/ex06/README.md](evidencias/ex06/README.md) reúne verificações HTTP, ambiente e pytest. O diagnóstico administrativo não concede acesso clínico. Hardening e SQLModel permanecem nos próximos exercícios; o Ex. 7 implementa M2M.

## Laboratório M2M — Exercício 7

Client Credentials em `POST /auth/m2m/token`, autenticado com Basic; bearer com audiência/tipo próprios e somente `disponibilidade:ler`. O laboratório consulta `GET /disponibilidade?dia=2026-10-15&profissional_id=1` e não acessa consultas clínicas, agenda humana ou administração.

Para habilitar localmente, execute `.venv/bin/python -m app.auth.provision_m2m`, copie o hash para `M2M_CLIENT_SECRET_HASH` no `.env` e reinicie o servidor. Sem hash, o M2M fica desativado e a autenticação humana continua funcionando. O segredo nunca entra no frontend, Git ou ZIP.

[Contrato, fluxo e regras aprovadas](docs/integracao-m2m.md): blocos de 30 minutos, dias úteis 08h–18h, fuso da clínica e cancelamento liberando horário. [Evidências do Ex. 7](evidencias/ex07/README.md) preservam execução HTTP/pytest sem bearer ou credenciais. Disponibilidade não é reserva nem garantia contra concorrência.

## Revisão manual OWASP — Exercício 8

[docs/vulnerabilidades.md](docs/vulnerabilidades.md) analisa três categorias distintas de OWASP Top 10:2021: acesso por objeto no histórico e headers/throttling ausentes no baseline atual. [Evidências](evidencias/ex08/README.md) guardam snapshots com revisão/hash, payloads, respostas, execução e print, sem scanner ou mudanças em `app/`.

O cenário de paciente autenticado é demonstrado somente em experimento didático separado, autorizado pelo responsável pelo projeto. A aplicação não ganhou papel/portal de paciente; aceitação acadêmica desse enquadramento permanece pendente. O relatório não inventa SQL Injection ou XSS explorado e identifica quais correções pertencem às próximas etapas.

## Correções de entrada e saída — Exercício 9

Schemas de consultas e formulário M2M rejeitam extras; status permite apenas `agendada`, `cancelada`, `realizada`, e username do login usa regex ASCII. Middleware JWT estabelece identidade humana/M2M uma vez por requisição; ownership continua centralizado antes de acesso/mutação. Cookie é exclusivo da agenda e não contorna um cabeçalho inválido. HTML legado mantém auto-escape.

[Correções, comparações e pendências](docs/correcoes-entrada-saida.md) e [evidências reproduzíveis](evidencias/ex09/README.md) distinguem código real de SQL/BOLA didáticos isolados. `/auth/m2m/token` foi aprovado como endpoint adicional para corrigir o mesmo padrão de extras. Hardening Ex. 10 e persistência SQLModel Ex. 11 continuam pendentes, assim como aceite acadêmico dos experimentos; não há aprovação de deploy.
