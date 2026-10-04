# Exercício 10 — Rede e proteção contra abuso

## Configuração e justificativa

| Controle | Configuração adotada | Motivo |
| --- | --- | --- |
| CORS | `CORS_ORIGINS=["http://localhost:5173"]` | Origem explícita de demonstração; não há frontend novo |
| Métodos | GET, POST, PATCH, DELETE | Operações usadas pela aplicação |
| Headers de entrada | Authorization e Content-Type, além dos headers CORS simples | Bearer e JSON/Form existentes |
| Credenciais CORS | `allow_credentials=False` | API usa bearer explícito; cookie permanece exclusivo da agenda no mesmo site |
| Headers de saída expostos | Retry-After | Consumidor permitido pode conhecer quando tentar novamente |
| Frame | `X-Frame-Options: DENY` | A agenda não precisa ser embutida em frames |
| MIME | `X-Content-Type-Options: nosniff` | Impedir inferência indevida do tipo de conteúdo |
| HSTS | `max-age=31536000`, somente HTTPS | Política de um ano, sem assumir controle de subdomínios ou preload |
| Credenciais | 5 requisições em 60 segundos por IP | Limitar a sequência de força bruta observada no Ex. 8 |
| Geral | 60 requisições em 60 segundos por IP | Diferenciar leitura/CRUD dos endpoints de credenciais |

Origem, limites e valores dos headers são **recomendações de engenharia adotadas no projeto**; o enunciado exige os controles, sem determinar esses números. São parâmetros para demonstração local, não capacidade ou adequação de produção medida. Os limites podem ser alterados por `LOGIN_RATE_LIMIT` e `GENERAL_RATE_LIMIT`; a janela permanece 60 segundos. Settings rejeita cotas não positivas ou uma cota de credenciais igual/maior que a geral.

`Settings` valida origens HTTP(S) completas, sem wildcard, usuário/senha, caminho ou fragmentos, com porta válida. Configuração por `.env.example` é pública; `.env` e credenciais locais nunca entram no Git ou ZIP.

## Fluxo HTTP

`app/network.py` usa middleware ASGI e o `CORSMiddleware` do Starlette. A composição é:

```text
Headers de segurança
    → CORS / preflight
        → rate limiting
            → middleware JWT
                → validação, autorização e operação
```

Preflight permitido responde sem exigir JWT e não consome cota; preflight com origem, método ou header proibido retorna 400. Uma requisição simples de origem externa pode continuar retornando HTTP 200, mas sem `Access-Control-Allow-Origin`. CORS restringe o acesso do navegador à resposta, não autentica o cliente nem impede chamadas de curl/laboratório.

Origin permitido não dispensa bearer: `/consultas` sem JWT continua 401. Métodos/scopes/papéis e ownership existentes permanecem aplicados. Os headers acompanham preflight, HTML autorizado e respostas verificadas 200, 400, 401, 403, 404, 422 e 429. Exceções internas inesperadas/500 e comportamento de proxy serão revisados na integração/auditoria final; não extrapolar essa cobertura.

## Limitação de requisições

O limitador usa janela móvel de 60 segundos, relógio monotônico, filas de instantes e lock para a checagem/gravação conjunta. Cada cliente tem duas cotas independentes: `credenciais` e `geral`.

- `/auth/token`, `/auth/m2m/token` e `/auth/mfa` compartilham a cota de cinco, incluindo sucesso, erro de credencial e entrada inválida. Evita transferir tentativas de login para outro endpoint de autenticação.
- As demais requisições, incluindo diagnóstico e documentação, usam a cota de 60. Preflight CORS é atendido antes do limitador.
- Ao exceder a cota, retornar 429, `Retry-After` inteiro arredondado para cima e `Cache-Control: no-store`, antes de bcrypt/JWT/operação.
- Negativas 429 não acrescentam tentativas nem prolongam a janela. Requisições aceitas voltam a consumir cota após o período pertinente.
- A chave usa o endereço de `request.client`; `X-Forwarded-For` não é lido pelo limitador. A configuração padrão de proxy do Uvicorn pode transformar esse endereço; para a demonstração direta, usar `--no-proxy-headers`.
- Estado novo a cada lifespan; entradas inativas são removidas. Não há persistência ou coordenação entre processos.

**Limitações:** usuários atrás de NAT compartilham IP e podem bloquear uns aos outros; atacante distribuído pode trocar IPs; reiniciar o processo ou usar vários workers altera a proteção. Muitos IPs ativos ainda podem pressionar memória/CPU. Não apresentar esse contador como defesa completa de disponibilidade ou bloqueio definitivo de força bruta. Estes riscos devem entrar na decisão do Capstone.

## HTTPS e HSTS

HSTS é enviado somente quando o esquema ASGI é HTTPS. Não habilita TLS, não protege a primeira conexão HTTP e não substitui certificado válido. IPs não são hosts HSTS de navegador. A evidência usa `https://clinica.example` no TestClient para verificar a resposta, sem handshake, certificado ou navegador real. O HTTP local recebe DENY/nosniff, sem HSTS.

Com proxy TLS futuro, confiar apenas no proxy configurado e verificar a representação correta do esquema/IP. `includeSubDomains`, preload e redirecionamento HTTPS não foram adicionados sem um domínio/topologia de implantação definidos. A especificação é a [RFC 6797](https://www.rfc-editor.org/rfc/rfc6797), especialmente tratamento em transporte seguro/inseguro; o [CORS do FastAPI](https://fastapi.tiangolo.com/tutorial/cors/) descreve a configuração de origens e credenciais.

## Findings e rastreabilidade

| Finding / requisito | Ameaça / controle / teste | Resultado |
| --- | --- | --- |
| VUL-002 / R17 | TM-012, CTRL-11, TEST-15 | DENY/nosniff nas respostas verificadas; HSTS em HTTPS em processo; TLS real pendente |
| VUL-003 / R17 | TM-016/008, CTRL-07, TEST-14 | Das mesmas 20 tentativas inválidas, primeiras cinco → 401, demais → 429; senha correta aguarda janela; depois → 200 |
| CORS / REQ-10 | CTRL-11, TEST-15 | Origem exata e preflight verificados; origem negada sem concessão; JWT permanece obrigatório |

`tests/test_hardening.py` acrescenta 31 casos. A suíte integrada passou em **163 testes**, com dois avisos de dependências. Um teste anterior de cinco erros MFA avança somente o relógio do limitador: verifica o orçamento do desafio sem ser interrompido pela cota HTTP; a cota real é exercitada pelos testes de hardening.

[Evidências](../evidencias/ex10/README.md): 35 observações HTTP, versão/configuração, sequência de abuso, recuperação, HTML e saída pytest. Nenhum teste de carga, scan ZAP, TLS real, pipeline ou deploy foi executado neste exercício. SQLModel continua no Ex. 11; lacunas acadêmicas dos Ex. 8/9 permanecem explicitadas nos respectivos relatórios.
