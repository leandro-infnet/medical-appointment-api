# Laboratório M2M — Exercício 7

Client Credentials foi escolhido porque o laboratório age em nome próprio, sem delegação humana. Authorization Code atenderia outro cenário; compartilhar senha profissional confundiria identidade e privilégios. Referência: [RFC 6749, §4.4](https://www.rfc-editor.org/rfc/rfc6749#section-4.4).

## Contratos separados

| Elemento | Humano | Laboratório |
| --- | --- | --- |
| Emissão | `/auth/token`, admin conclui `/auth/mfa` | `/auth/m2m/token`, grant client_credentials |
| Credencial | Conta/senha bcrypt | Basic com client ID e segredo bcrypt |
| Audiência | `clinic-human-clients` | `clinic-laboratory` |
| Subject / finalidade | Username / human_access | `client:<id>` / m2m_access |
| Claims específicas | `amr` | `client_id`, `scope` |
| TTL padrão | 15 min | 5 min (1–15) |
| Permissão | Papel, vínculo e recurso | Somente `disponibilidade:ler` |

HS256 e as claims comuns (`sub`, `exp`, `iat`, `nbf`, `iss`, `aud`, `jti`, `token_use`) são validados no servidor. Tokens humanos/M2M não são intercambiáveis. Scope omitido concede o mínimo; scope vazio emite token sem permissão; scope adicional solicitado gera 400. Bearer com scope insuficiente/excessivo gera 403 e `insufficient_scope`.

Basic ausente/inválido: 401 `invalid_client`; grant indevido: 400 `unsupported_grant_type`; grant ausente ou campo extra: 422. Não há refresh token. `SecurityScopes` aplica a permissão; o esquema OpenAPI apenas a documenta.

## Configurar e usar

1. Executar `.venv/bin/python -m app.auth.provision_m2m` com segredo fictício de 8–72 bytes UTF-8.
2. Guardar o hash em `M2M_CLIENT_SECRET_HASH` no `.env`, definir `M2M_CLIENT_ID` e reiniciar. Hash ausente/vazio desativa M2M sem interromper login humano.
3. Solicitar POST `/auth/m2m/token` com Basic e formulário `grant_type=client_credentials`, `scope=disponibilidade:ler`.
4. Usar bearer no GET `/disponibilidade?dia=2026-10-20&profissional_id=1`.

Client ID/segredo devem passar por codificação de formulário antes de Basic/base64 ([RFC 6749, §2.3.1](https://www.rfc-editor.org/rfc/rfc6749#section-2.3.1)); usar segredo URL-safe simplifica a demonstração. Basic exige TLS para exposição externa. Segredo/hash/token ficam fora de frontend, URLs, Git e ZIP.

## Disponibilidade e dados mínimos

Escolha de domínio DEC-19: blocos de 30 min, dias úteis 08h–18h, `America/Sao_Paulo`. Cancelada libera horário; demais estados bloqueiam. São 20 slots, com início inclusivo/fim exclusivo; consulta 08:15–08:45 bloqueia dois slots. Comparação: `slot.inicio < consulta.fim` e `slot.fim > consulta.inicio`. Offset é convertido antes do cálculo; sem offset, interpretar como horário local.

Resposta: `profissional_id`, `dia`, `fuso`, `intervalos` com início/fim. Sem paciente, motivo, notas ou ID de consulta; no-store. Profissional desconhecido: 404; data/ID inválido: 422. Sem calendário de feriados ou duração variável.

A disponibilidade lê o mesmo SQLite do CRUD por sessão injetada. A leitura não reserva intervalo; a escrita usa a proteção de sobreposição descrita em [persistência](persistencia.md).

## Verificação e limites

`auth/m2m.py` autentica/autoriza; `tokens.py` valida claims; `database/disponibilidade.py` calcula intervalos; rota e response model reduzem saída. `test_m2m.py` cobre scopes, credenciais/grant, assinatura, claims, expiração, cliente desativado, acesso cruzado e regras de horário. [Ex. 7](../evidencias/ex07/README.md): 101 testes integrados e 20 cenários HTTP históricos; TM-014/CTRL-10/TEST-11.

Tokens roubados permitem leitura até expiração/desativação. Trocar hash não revoga bearer; chave comprometida afeta ambos os tipos de token. Intervalos podem revelar ocupação indiretamente. TLS real e demais riscos estão no [capstone](relatorio-capstone.md). Referência de implementação: [FastAPI SecurityScopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/).
