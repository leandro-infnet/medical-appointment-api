# Autenticação e autorização — Exercício 6

OAuth2PasswordBearer extrai o bearer; bcrypt verifica a senha; JWT identifica a conta. A autorização combina RBAC, atributos confiáveis de vínculo e ownership em `app/auth/policies.py`.

## Permissões e escolha

| Ator | Acesso |
| --- | --- |
| Profissional | CRUD apenas quando o profissional do recurso corresponde à conta e há vínculo paciente/profissional |
| Recepção | Agenda HTML com IDs, horário e status; sem motivo/notas |
| Administrador | Diagnóstico `/admin/status` após MFA simulado; sem acesso clínico |
| Anônimo | 401 nos recursos protegidos |

RBAC sozinho permitiria acesso entre profissionais; uma linguagem ABAC genérica seria complexidade desnecessária. Os vínculos `(1,1)`, `(2,1)`, `(2,2)` ficam no servidor, sem endpoint de alteração. Identidade/papel não vêm do corpo. Listagens aplicam o mesmo escopo, e PATCH não altera vínculos.

Sem identidade: 401 e `WWW-Authenticate: Bearer`. Papel ou vínculo proibido na criação: 403. Recurso alheio/inexistente em GET/PATCH/DELETE: mesmo 404, antes de exposição ou mutação.

## Configuração local

1. Instalar dependências, copiar `.env.example` para `.env` e definir `JWT_SECRET` aleatória com pelo menos 32 bytes.
2. Definir `MFA_SIMULATED_CODE` com seis dígitos fictícios. Em HTTP local, usar `AGENDA_COOKIE_SECURE=false`; padrão true exige HTTPS.
3. Executar `.venv/bin/python -m app.auth.provision` e cadastrar senhas fictícias de 8–72 bytes UTF-8. O arquivo `.local/usuarios.json` não é sobrescrito e recebe 0600 quando suportado.
4. Iniciar Uvicorn pelo README. Falta de configuração/cadastro válido impede startup.

Excluir `.env`, cadastro, hashes, tokens e credenciais reais do Git/ZIP. O cadastro é carregado no startup; mudanças no arquivo exigem restart.

## Senhas, token e MFA

- bcrypt: salt aleatório, custo 12; fixtures efêmeras usam 4. Senhas acima de 72 bytes não são truncadas. Credencial incorreta, conta ausente/inativa compartilham erro; nome ausente também passa por comparação com hash fictício.
- JWT: HS256 fixado no servidor; TTL padrão 15 min (1–60). Claims obrigatórias: `sub`, `exp`, `iat`, `nbf`, `iss`, `aud`, `jti`, `token_use`, `amr`. Datas NumericDate inteiras; emissor `medical-appointment-api`, audiência `clinic-human-clients`, finalidade `human_access`.
- JWT não contém dados clínicos nem senhas. Conta ativa/papel vêm do cadastro confiável; admin exige `amr` pwd+mfa. Não há refresh nem revogação individual; logout não revoga token roubado.
- `POST /auth/token`, formulário password: profissional/recepção recebem 200; admin recebe 202 com desafio, sem bearer. `POST /auth/mfa` conclui o desafio e emite token admin.
- Desafio aleatório vinculado à conta: 300 s, uso único, cinco erros, substituído por novo login. O código local estático é apenas simulação; não equivale a MFA com dispositivo independente. Estado em memória, um worker.

## Sessão da agenda

Na Swagger, autenticar `recepcao`, executar `POST /auth/agenda-session` com bearer e abrir `/agenda?dia=2026-10-20` na mesma origem. `DELETE /auth/agenda-session` com bearer apaga o cookie. O diálogo OAuth da Swagger não conclui MFA: para admin, usar os endpoints explícitos.

Cookie `agenda_session`: HttpOnly, SameSite Strict, Secure por padrão, Path `/agenda`, sem Domain e com expiração JWT. Só autentica GET da agenda. JSON/admin e criação/exclusão da sessão exigem bearer. Authorization inválido não cai para cookie válido. Respostas protegidas usam no-store; futuras mutações por cookie exigem revisão de CSRF.

## Localização e verificação

`passwords.py`, `tokens.py`, `mfa.py` e `policies.py` concentram regras; `settings.py` carrega configuração; `database/identidades.py` mantém contas/vínculos. Desde o Ex. 9, `auth/middleware.py` valida identidade uma vez e as dependências consomem `request.state`; ownership permanece na política.

`tests/test_autorizacao.py` verifica acesso administrativo negado, ownership, assinatura/claims/expiração, bcrypt, MFA, contas e cookies. [Ex. 6](../evidencias/ex06/README.md): 60 testes e 21 cenários HTTP históricos. Laboratório em [M2M](integracao-m2m.md), cotas em [hardening](hardening.md), riscos de produção no [capstone](relatorio-capstone.md).

Referências: [FastAPI OAuth2/JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [bcrypt](https://pypi.org/project/bcrypt/), [PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html), [BaseSettings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
