# API de Agendamento de Consultas Médicas

API REST em FastAPI, com CRUD de consultas, agenda HTML em Jinja2 e disponibilidade para laboratório via OAuth 2.0 M2M. Consultas persistem em SQLModel/SQLite; autenticação usa bcrypt, JWT e MFA administrativo simulado.

## Instalação e execução local

Python 3.11+; desenvolvimento e testes em Python 3.14. Dependências declaradas no `pyproject.toml`, sem lockfile.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Configurar `JWT_SECRET` com chave aleatória de pelo menos 32 bytes e `MFA_SIMULATED_CODE` com seis dígitos fictícios. Para gerar uma chave local:

```bash
.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))'
.venv/bin/python -m app.auth.provision
```

O provisionamento solicita senhas sem eco e cria `.local/usuarios.json` com hashes bcrypt. Configuração/cadastro inválidos impedem o startup. Para agenda no navegador em HTTP local, usar `AGENDA_COOKIE_SECURE=false`; o padrão é HTTPS.

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Documentação: [Swagger](http://127.0.0.1:8000/docs), [ReDoc](http://127.0.0.1:8000/redoc) e `/openapi.json`.

**Excluir `.env`, bancos, cadastro de contas, segredos, ambiente virtual e caches do Git/ZIP.** Manter `.env.example` sem credenciais reais.

## Acesso e regras

| Consumidor | Operação permitida |
| --- | --- |
| Profissional | CRUD JSON somente de consultas dos pacientes vinculados a ele |
| Recepção | Agenda diária HTML, sem motivo clínico ou notas internas |
| Administrador | `/admin/status` após MFA simulado, sem acesso clínico |
| Laboratório | Somente disponibilidade, com scope `disponibilidade:ler` |

- CRUD: `POST /consultas`, `GET /consultas`, `GET/PATCH/DELETE /consultas/{id}`.
- JSON de sucesso: `id`, `paciente_id`, `profissional_id`, `data_hora`, `motivo`, `status`. Notas internas e timestamps ficam fora da resposta.
- Agenda: após login como `recepcao`, executar `POST /auth/agenda-session` com bearer e abrir `/agenda?dia=2026-10-20`. Logout: `DELETE /auth/agenda-session` com bearer.
- Login admin: `/auth/token` devolve desafio 202; concluir `/auth/mfa` antes de usar o bearer administrativo.
- Consultas de 30 minutos no fuso `America/Sao_Paulo`; canceladas liberam horário. Sobreposição para o mesmo profissional gera 409, inclusive no PATCH.
- Disponibilidade: dias úteis, 08h–18h, por profissional. A consulta de disponibilidade não reserva horário; o CRUD não restringe expediente/fim de semana.

[Contrato humano](docs/autenticacao-autorizacao.md) e [contrato M2M](docs/integracao-m2m.md).

### Habilitar laboratório

Executar `.venv/bin/python -m app.auth.provision_m2m`, copiar o hash para `M2M_CLIENT_SECRET_HASH` no `.env` e reiniciar. Sem hash, M2M fica desativado. Solicitar token em `POST /auth/m2m/token` com Basic e formulário `grant_type=client_credentials`; usar o bearer em `/disponibilidade?dia=2026-10-20&profissional_id=1`.

## Testes e pipeline

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pip install -e '.[dev,security]'
.venv/bin/python -m pip install --upgrade 'pip>=26.2,<27'
.venv/bin/python scripts/security_gate.py
```

GitHub Actions executa pytest, Bandit e pip-audit. Falhas/skips, Bandit HIGH, advisory SCA não triado ou análise incompleta bloqueiam o gate. A proteção da `main` exige o check **Security gate**; o [PR de demonstração](evidencias/ex12/github-actions.md) registra merge bloqueado. Relatórios transitórios: `reports/security/`.

## Documentação e evidências

| Tema | Documento |
| --- | --- |
| Escopo e permissões | [Requisitos](docs/requisitos.md) |
| Fundamentos e arquitetura | [CIA/DFD](docs/cia-dfd.md), [STRIDE](docs/threat-model.md), [partições](docs/arquitetura-seguranca.md) |
| Revisão e correções | [Vulnerabilidades](docs/vulnerabilidades.md), [entrada/saída](docs/correcoes-entrada-saida.md) |
| Controles | [Hardening](docs/hardening.md), [persistência](docs/persistencia.md), [DevSecOps](docs/devsecops.md) |
| Decisões e entrega final | [Decisões](docs/decisoes.md), [rastreabilidade](docs/rastreabilidade.md), [OpenAPI](docs/auditoria-openapi.md), [capstone](docs/relatorio-capstone.md) |

`app/routes/` trata HTTP; `models/` separa contratos/tabelas; `database/` gerencia sessões e operações; `auth/` centraliza identidade/políticas; `templates/` contém o HTML. Testes em `tests/`, evidências por etapa em `evidencias/ex01/` a `ex13/`. Scripts históricos devem rodar nos respectivos baselines, preservando as saídas anteriores.

## Entrega

O [capstone](docs/relatorio-capstone.md) registra ZAP passivo antes/depois, mocking, auditoria OpenAPI e riscos residuais. **Produção bloqueada:** TLS real, identidade/MFA de produção, auditoria persistente e recuperação operacional pendentes. O gate aprovado não encerra esses riscos.

- [x] Vídeo de até cinco minutos, no YouTube listado, com link na entrega.
- [x] ZIP final `leandro_medeiros_DR2_AT.ZIP`, revisado e sem segredos.

📹 [Vídeo no YouTube](https://youtu.be/LOaATrkbHro)  
☁️ [Pasta de apoio ao vídeo no Google Drive](https://drive.google.com/drive/u/0/folders/1fREoLUQ0jaFfAfYo3vyfTCJTrspcyotq)
