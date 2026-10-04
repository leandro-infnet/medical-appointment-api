# Autenticação e autorização — Exercício 6

> Este documento preserva o contrato humano do Ex. 6. O laboratório, mencionado como futuro neste baseline, foi implementado no Ex. 7 com [contrato próprio](integracao-m2m.md).


## Resultado, requisitos e contrato

A aplicação mantém o CRUD, os response models e a agenda com escape. Agora exige identidade humana válida e autoriza por papel e recurso. Este incremento implementa OAuth2PasswordBearer, bcrypt, JWT expirável, ownership, MFA administrativo simulado e pytest de negação a não administrador (R10/R11; fundação de R22).

**Decisão aprovada pelo responsável pelo projeto:** profissional lê/cria/atualiza/remove apenas consultas de seus pacientes vinculados; recepção só lê agenda mínima; administrador só acessa diagnóstico sem informação clínica. As escolhas de biblioteca, parâmetros e transporte abaixo são **recomendações de engenharia adotadas**, não exigências adicionais da disciplina.

| Ator | CRUD JSON | Agenda HTML | `/admin/status` | Login |
| --- | --- | --- | --- | --- |
| Profissional | Somente se `consulta.profissional_id == identidade.profissional_id` e vínculo confiável paciente/profissional | Negado | Negado | Senha → bearer |
| Recepcionista | Negado | Permitido; sem motivo/notas | Negado | Senha → bearer → cookie opcional |
| Administrador | Negado | Negado | Permitido após MFA simulado | Senha → desafio → fator → bearer |
| Anônimo | 401 | 401 | 401 | Pode iniciar login/MFA, sem acesso concedido automaticamente |

Paciente autenticado e laboratório não são contas implementadas nesta etapa. A ambiguidade do paciente no cenário BOLA precisa ser resolvida antes do Ex. 8; o laboratório terá fluxo próprio no Ex. 7.

## Modelo escolhido: RBAC + atributos e autorização por recurso

Autenticação responde quem é o usuário; autorização decide o que pode fazer. RBAC decide quais famílias de operações o papel pode executar. Ownership é a verificação concreta do recurso, não um papel: a consulta deve pertencer ao profissional autenticado. A verificação de vínculo é baseada em atributos confiáveis (ABAC), inclusive na criação, quando ainda não existe consulta.

RBAC isolado permitiria que qualquer profissional acessasse qualquer ID. ABAC genérico com linguagem de políticas seria complexidade desnecessária. A combinação mínima está em `app/auth/policies.py`: papel, profissional do registro e relacionamento servidor. Papéis e IDs profissionais vêm do cadastro local, nunca do corpo ou de uma claim fornecida pelo cliente. Não há autoatribuição de papel ou endpoint público de cadastro.

`app/database/identidades.py` registra vínculos fictícios `(paciente, profissional)`: `(1,1)`, `(2,1)`, `(2,2)`. Eles são dados de demonstração aprovados, não regra acadêmica de exclusividade de paciente. Sua gestão fica no servidor, sem rota de alteração. A listagem restringe primeiro por profissional no acesso aos dados e verifica também o vínculo antes da saída; filtros não ampliam permissão. PATCH não admite mudança de vínculo no contrato atual.

Sem identidade válida: 401 e `WWW-Authenticate: Bearer`. Papel inadequado/criação com vínculo proibido: 403. Leitura, PATCH e DELETE de recurso alheio ou ausente: mesma resposta 404, para não revelar existência. A autorização ocorre antes de exposição ou mutação.

## Organização e configuração

| Arquivo | Responsabilidade |
| --- | --- |
| `app/settings.py` | BaseSettings, segredo obrigatório, TTL e configuração local |
| `app/models/identidades.py` | Conta imutável; contratos de token/desafio/fator; entrada MFA com campos extras proibidos |
| `app/database/identidades.py` | Leitura e validação do cadastro local e vínculos confiáveis |
| `app/auth/passwords.py` | Hash e comparação bcrypt |
| `app/auth/tokens.py` | Única emissão/validação de JWT |
| `app/auth/dependencies.py` | Principal humano obtido do cadastro; bearer JSON e cookie HTML usam o mesmo validador |
| `app/auth/policies.py` | Papel, vínculo e recurso autorizado |
| `app/auth/mfa.py` | Desafio temporário com lock, expiração, uso único e tentativas limitadas |
| `app/auth/provision.py` | Criação interativa das quatro contas fictícias locais |
| `app/routes/auth.py`, `admin.py` | Contratos HTTP de login, MFA, sessão e diagnóstico |
| `app/main.py` | Startup validando configuração/cadastro, roteadores e estado MFA |

Não há middleware JWT ainda: a proteção é feita por dependências com `Annotated`. O Ex. 9 reutilizará o validador central, preservando a autorização por recurso. SQLModel continua previsto no Ex. 11; o arquivo de contas não é apresentado como persistência relacional.

### Preparar execução local

1. Instalar `.venv/bin/python -m pip install -e '.[dev]'`.
2. Copiar `.env.example` para `.env`.
3. Gerar uma chave local com `.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))'` e configurar `JWT_SECRET`. Não guardar essa saída em evidências.
4. Definir `MFA_SIMULATED_CODE` com seis dígitos fictícios, somente no `.env` local.
5. Em HTTP local, definir explicitamente `AGENDA_COOKIE_SECURE=false`. O padrão é `true` e requer HTTPS para o navegador enviar o cookie.
6. Executar `.venv/bin/python -m app.auth.provision`. Informar senhas fictícias (8–72 bytes UTF-8) e confirmar cada uma. O cadastro não sobrescreve arquivo existente; usa permissões 0600 quando suportadas.
7. Iniciar Uvicorn pelo comando do README. Segredo/código ausente ou cadastro inexistente interrompe o startup. Não existe chave padrão previsível.

**Nenhuma credencial real deve entrar no repositório ou no ZIP.** `.env`, variantes locais e `.local/` são ignorados; `.env.example` é versionado sem valores secretos. Hashes também são material sensível: excluir o cadastro da entrega, não só as senhas. Provisionar novamente em ambiente isolado.

## Senhas e JWT

bcrypt usa salt aleatório e custo 12 no provisionamento/startup. Testes usam custo 4 somente para reduzir tempo em cadastro efêmero; não alteram o padrão da aplicação. O limite é em bytes UTF-8, sem truncamento: bcrypt 5 rejeita entradas acima de 72 bytes. Login fora da faixa retorna 401, não erro interno. Senha incorreta, usuário ausente e conta desativada compartilham mensagem; hash fictício cobre a verificação de nome inexistente. Isso reduz enumeração, sem prometer tempo idêntico.

HS256 é fixado pelo servidor; o algoritmo recebido não escolhe como verificar assinatura. Chave deve ter ao menos 32 bytes. TTL padrão: 15 minutos, configurável de 1 a 60. Claims obrigatórias: `sub`, `exp`, `iat`, `nbf`, `iss`, `aud`, `jti`, `token_use`, `amr`. Datas são NumericDate inteiras; `sub`/`jti` não vazios. Emissor `medical-appointment-api`, audiência `clinic-human-clients`, finalidade `human_access`, métodos `pwd` ou `pwd+mfa`. JWT é assinado, não cifrado: não inclui motivo, paciente, senha, hash ou código.

Cada requisição verifica assinatura, algoritmo, datas, emissor, audiência, finalidade e conta ativa no cadastro confiável. Administrador exige `amr` com MFA; só a presença do nome do papel não basta. As permissões são lidas do servidor. Desativação em memória invalida acesso imediatamente; edição do arquivo só é carregada no reinício. Não há revogação individual por `jti`, refresh token ou troca de senha por API. Token roubado pode ser usado até expiração/desativação; trocar chave invalida todos.

## Fluxo HTTP e MFA simulado

`POST /auth/token`: formulário `grant_type=password`, `username`, `password`. Profissional/recepção recebem 200 com bearer e `expires_in`. Administrador recebe 202 com `challenge_id` e duração de 300 segundos, **sem access_token**. `POST /auth/mfa`: JSON com desafio e código configurado; sucesso emite token administrativo. Respostas de emissão usam `Cache-Control: no-store` e `Pragma: no-cache`.

O desafio é opaco e aleatório, não é bearer e fica vinculado à conta. Expira em cinco minutos, é consumido atomicamente após sucesso, é invalidado após cinco erros e um novo login administrativo substitui o anterior. Nenhum segundo fator aparece na resposta. Código configurado é um **simulador estático para dados fictícios**, sem dispositivo independente, entrega externa ou proteção equivalente a TOTP/WebAuthn. Não é MFA de produção.

**Limites:** desafio em memória é perdido no restart e não é compartilhado entre workers. Novo login pode renovar o limite de tentativas; rate limiting global/login será Ex. 10. Reiniciar com uma chave inalterada não revoga tokens já emitidos. Usar um worker e localhost nesta demonstração; não liberar produção.

## Cookie da agenda e CSRF

1. Na Swagger UI, usar **Authorize** com a conta `recepcao` (fluxo password).
2. Executar `POST /auth/agenda-session` com o bearer autorizado.
3. Abrir `/agenda?dia=2026-10-15` na mesma origem/navegador. O cookie permite GET e navegação pelo filtro de data; não colocar token na URL.
4. Executar `DELETE /auth/agenda-session` com bearer da recepção para remover o cookie.

O cookie possui HttpOnly, SameSite Strict, Path `/agenda`, sem Domain e Secure por padrão; expira junto com o JWT. `Cache-Control: no-store` protege a agenda contra armazenamento em caches conformes. Cookie só é aceito na dependência da agenda GET; CRUD, sessão e admin continuam exigindo Authorization. Criação/remoção de sessão exige bearer e papel de recepção, impedindo login via formulário cross-site sem Authorization. SameSite não substitui autorização. Um bearer inválido enviado explicitamente não cai silenciosamente para o cookie.

**Risco residual de sessão:** logout remove o cookie do navegador, sem revogar uma cópia roubada do JWT. Path limita envio pelo navegador, não é isolamento de origem. Se futuramente a agenda aceitar mutações com cookie, será necessário reavaliar CSRF e implementar proteção específica antes dessa mudança. Nenhuma mutação atual aceita autenticação por cookie.

## Testes, evidências e continuidade

`tests/test_autorizacao.py` verifica casos permitidos/negados, incluindo o pytest exigido de não administrador, senhas e tamanho UTF-8, claims/assinatura/algoritmo, MFA/replay/expiração/tentativas, vínculos na criação, recurso alheio sem mutação, filtragem, contas desativadas e cookie seguro/inválido/encerrado. Os testes dos Ex. 1/2 usam login real, sem override de autenticação; a projeção JSON e o XSS HTML continuam verificados.

A evidência HTTP usa `TestClient`, em processo, sem servidor remoto, em armazenamento isolado. Respostas registradas omitem bearer, senha, hashes, desafios e fator. [Evidências e comandos](../evidencias/ex06/README.md) e [rastreabilidade](rastreabilidade.md) separam execução de pendências. Não houve scan, MFA real, teste concorrente de banco, TLS de produção ou auditoria completa OpenAPI.

Reutilização: verificador e distinção de finalidade no Ex. 7; ownership nos ataques dos Ex. 8/9; middleware no Ex. 9; login e sessões no hardening do Ex. 10; contas/vínculos e dados no SQLModel do Ex. 11; suíte e Threat IDs no Ex. 12/13. Para login administrativo, concluir MFA pelo endpoint explícito e então inserir bearer no cliente HTTP; o diálogo OAuth da Swagger não completa MFA automaticamente.

## Referências técnicas

- [FastAPI: OAuth2 e JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/). A biblioteca de senha ilustrada no tutorial não substitui o bcrypt exigido neste projeto.
- [bcrypt: documentação e limite de senha](https://pypi.org/project/bcrypt/).
- [PyJWT: validação de claims](https://pyjwt.readthedocs.io/en/stable/usage.html).
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
