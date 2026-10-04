# Integração do laboratório — Exercício 7

## Requisito e decisão

O Exercício 7 exige selecionar/implementar OAuth 2.0 M2M e diferenciar o laboratório de profissionais humanos por scopes e claims (R12). O laboratório consome apenas disponibilidade: não recebe pacientes, consultas clínicas, prontuários, notas ou poder administrativo.

**Recomendação de engenharia adotada:** Client Credentials, pois o cliente confidencial age em nome próprio, sem delegação de usuário. Authorization Code serve delegação com usuário; compartilhar a senha de um profissional confundiria identidade e privilégio. A escolha é fundamentada na [RFC 6749, seção 4.4](https://www.rfc-editor.org/rfc/rfc6749#section-4.4). O endpoint é separado do login humano para preservar o contrato de senha/MFA já existente.

## Contrato de autenticação e autorização

| Elemento | Humano | Laboratório |
| --- | --- | --- |
| Emissão | `/auth/token`, senha; admin conclui `/auth/mfa` | `/auth/m2m/token`, `grant_type=client_credentials` |
| Autenticação na emissão | Conta humana e bcrypt | HTTP Basic, client ID confiável e segredo verificado com bcrypt |
| Audiência | `JWT_AUDIENCE`, padrão `clinic-human-clients` | `clinic-laboratory`, exclusiva |
| `sub` | Username confiável | `client:<M2M_CLIENT_ID>` |
| `token_use` | `human_access` | `m2m_access` |
| Claims específicas | `amr` pwd / pwd+mfa | `client_id` e `scope` |
| Expiração padrão | 15 minutos | 5 minutos, configuração limitada a 1–15 |
| Permissão | Papel e vínculo/ownership consultados no servidor | Somente `disponibilidade:ler` concedido no servidor |
| Transporte no recurso | Bearer; cookie só em agenda GET | Bearer exclusivamente |

Ambos usam HS256 fixado pelo servidor e o mesmo verificador de assinatura/claims comuns: `sub`, `exp`, `iat`, `nbf`, `iss`, `aud`, `jti`, `token_use`. Audiência deve ser exatamente a esperada, não lista contendo diferentes consumidores. O contrato humano também continua exigindo `amr`; o M2M exige client ID, subject correspondente e scope textual. Tipo/audiência não são escolhidos pelo payload para determinar qual contrato validar.

Cliente ausente/desativado, segredo inválido, Basic malformado ou credenciais apenas no corpo → 401 com `WWW-Authenticate: Basic`, `{"error":"invalid_client"}`. Grant indevido → 400 `unsupported_grant_type`. Scope não autorizado solicitado → 400 `invalid_scope`. Campo grant ausente segue validação HTTP do FastAPI (422). Respostas do protocolo M2M têm `error` no nível superior; erros do login humano mantêm seu contrato anterior.

Scope omitido concede o padrão mínimo `disponibilidade:ler`; scope explicitamente vazio concede token sem acesso à disponibilidade e é negado com 403 ao tentar ler. Solicitar permissões não é recebê-las automaticamente. O servidor recusa qualquer scope adicional; token válido com scope ausente/insuficiente/excessivo não autoriza acesso. O header de negação inclui `insufficient_scope` e o escopo necessário. Não existe refresh token.

Mesmo um bearer M2M legítimo é recusado por consultas GET/listagem/POST/PATCH/DELETE, agenda, sessão HTML e administração. Tokens humanos são recusados na disponibilidade, inclusive quando o payload de um teste assinado adiciona o nome do scope. Saber um scope não transforma a identidade.

## Configuração e uso local

O M2M fica desativado se `M2M_CLIENT_SECRET_HASH` estiver ausente/vazio; isso não impede o startup e o funcionamento humano do Ex. 6. Não existe credencial padrão. Para habilitar:

1. Executar `.venv/bin/python -m app.auth.provision_m2m`.
2. Informar/confirmar segredo **fictício** (8–72 bytes UTF-8); o prompt não exibe o segredo.
3. Copiar o hash bcrypt gerado para `M2M_CLIENT_SECRET_HASH` no `.env` local. A saída é sensível: não salvar em evidências/Git/ZIP. O script não sobrescreve o `.env` nem o cadastro humano.
4. Configurar `M2M_CLIENT_ID=laboratorio_parceiro` e `M2M_TOKEN_MINUTES=5`; reiniciar Uvicorn para recarregar configurações.
5. No cliente HTTP, enviar POST `/auth/m2m/token` com autenticação Basic e formulário `grant_type=client_credentials`, `scope=disponibilidade:ler`.
6. Usar o access token como `Authorization: Bearer ...` no GET `/disponibilidade?dia=2026-10-15&profissional_id=1`.

Conforme o contrato Basic OAuth, client ID e segredo são codificados como formulário (`quote_plus`) **antes** de compor o Basic/base64 (RFC 6749, seção 2.3.1). Clientes que usem caracteres `+`, `%` ou não ASCII no segredo devem aplicar essa codificação. Preferir segredo fictício aleatório em alfabeto URL-safe para demonstração. Basic/base64 não cifra credenciais: exposição externa exige TLS. Não colocar segredo/token na URL ou compartilhar com frontend/navegador; o parceiro mantém a credencial no seu backend.

A Swagger descreve `LaboratorioOAuth2` com fluxo Client Credentials e scope na operação protegida; o token endpoint documenta Basic. Metadados OpenAPI não implementam autorização: os testes exercitam o comportamento real.

## Regra de disponibilidade aprovada

**Decisão de domínio aprovada pelo responsável pelo projeto — DEC-19:** agenda de demonstração com duração fixa de 30 minutos, segunda a sexta, 08h–18h e fuso `America/Sao_Paulo`. Somente `cancelada` libera horário; qualquer outro estado bloqueia conservadoramente. A consulta do parceiro retorna intervalos livres por profissional, sem paciente ou motivo.

Não é uma regra adicional imposta pela disciplina. A API calcula 20 slots diários alinhados ao expediente, com início inclusivo/fim exclusivo. Um registro às 08:15 ocupa 08:15–08:45 e bloqueia tanto 08:00–08:30 quanto 08:30–09:00. A comparação `slot.inicio < consulta.fim` e `slot.fim > consulta.inicio` considera sobreposição, não só igualdade de início. Horários com offset são convertidos ao fuso da clínica; os sem offset são locais. Sábado/domingo retornam lista vazia; não há calendário de feriados definido.

Resposta permitida: `profissional_id`, `dia`, `fuso` e `intervalos`, cada um com `inicio`/`fim` e offset. O ID profissional precisa constar no cadastro fictício; desconhecido retorna 404 e data/ID inválido retorna 422. Não há nomes, paciente, motivo, consulta ID, hashes ou notas na saída. Respostas usam no-store.

**Limites de negócio:** consulta disponível não é reserva nem garantia de exclusividade. O CRUD ainda não impede gravações sobrepostas, fora de expediente ou em fins de semana; endurecer essas invariantes exige decisão/constraints/teste com o banco no Ex. 11. Não foi alterado o contrato de status livre dos incrementos anteriores: desconhecidos bloqueiam, e XSS continua sendo tratado por escape na agenda. Regras de feriados, duração variável e validade futura de datas permanecem decisões a definir.

## Responsabilidades e segurança

- `app/auth/m2m.py`: Basic do cliente, erros OAuth e autorização com `SecurityScopes`; parser Basic adaptado somente para devolver o erro do protocolo, preservando OpenAPI.
- `app/auth/tokens.py`: emissão e validação centralizadas, mantendo contratos humano/M2M separados sobre verificações comuns.
- `app/settings.py`: cliente configurado no servidor, hash protegido e TTL; nenhum registro de laboratório como usuário humano.
- `app/routes/auth.py`: grant/scopes de emissão; no-store/no-cache, sem refresh.
- `app/models/disponibilidade.py`: allowlist explícita de saída do parceiro.
- `app/database/disponibilidade.py`: cálculo por intervalos, reutilizando snapshot das consultas em memória; não há integração de saída ou SQL nesta etapa.
- `app/routes/disponibilidade.py`: HTTP, profissional válido, autenticação/scope e response model mínimo.

O segredo bcrypt tem salt/custo 12 no provisionamento. Fixtures usam custo 4 somente no ambiente de teste. Remover a credencial da configuração e reiniciar desativa a identidade M2M, inclusive para tokens existentes. Trocar apenas o hash não revoga bearers emitidos; TTL curto limita a janela. Compartilhar chave de assinatura não concede audiência/tipo diferente sem assinatura válida, mas comprometer a chave compromete ambos: proteger/rotacionar esse segredo continua necessário.

## Threat model, verificação e continuidade

TM-014/CTRL-10/TEST-11 passam de planejados a implementados/verificados; SUP-08 e TB-03 representam o parceiro externo. O DFD mantém fluxos anteriores e adiciona a partição de disponibilidade e os fluxos do laboratório. Tokens/credenciais pertencem a AT-07.

Testes em `tests/test_m2m.py`: sucesso, scope padrão/explícito/vazio/excessivo, segredo e grant inválidos, assinatura/algoritmo/claims, expiração, confusão de identidade, escrita/leitura clínica negada, cliente desativado, schema/fluxo/scopes OpenAPI, limites/UTC/sobreposição/cancelamento/isolamento de profissional. Regressões humanas, CRUD e HTML também foram executadas. Evidências em [Ex. 7](../evidencias/ex07/README.md); matriz em [rastreabilidade](rastreabilidade.md).

Residual: disponibilidade revela ocupação indiretamente, sem identificar pacientes; bearer roubado continua lendo disponibilidade até expiração/desativação; não há rate limiting, revogação individual, TLS demonstrado, scanner, banco durável, garantia multiworker ou reserva atômica. Não há autorização para deploy. Ex. 9 deverá reutilizar ambos os verificadores no middleware; Ex. 10 aplica hardening também à emissão M2M; Ex. 11 persiste vínculos/consultas; Ex. 12/13 reutilizam TEST-11 e TM-014.

Referência complementar: [FastAPI: OAuth2 scopes e SecurityScopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/).

## Evolução da persistência — Exercício 11

A disponibilidade agora consulta o mesmo SQLite do CRUD por sessão injetada. O CRUD impede sobreposição de 30 minutos por profissional, inclusive atualização/reativação; retorna 409 e protege a gravação por reserva transacional. A disponibilidade permanece uma leitura, sem reservar o intervalo. Status desconhecido também é impedido pelo CHECK; a regra histórica defensiva do cálculo não enfraquece essa constraint. Vínculos permanecem no cadastro confiável estático, sem novo CRUD de identidade. Limites anteriores “sem SQL/rate limiting/validação de status” descrevem o baseline do Ex. 7. [Estado atual e testes](persistencia.md).
