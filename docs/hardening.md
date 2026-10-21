# Hardening — Exercício 10

## Configuração adotada

| Controle | Valor | Justificativa |
| --- | --- | --- |
| CORS | `CORS_ORIGINS=["http://localhost:5173"]` | Origem exata de demonstração; sem wildcard |
| Métodos/headers | GET/POST/PATCH/DELETE; Authorization/Content-Type | Contratos JSON/Form existentes |
| Credenciais CORS | false; expõe Retry-After | Bearer explícito; cookie somente na agenda de mesma origem |
| Enquadramento/MIME | X-Frame-Options DENY; X-Content-Type-Options nosniff | Agenda sem frames; impedir inferência de MIME |
| HSTS | max-age=31536000, somente HTTPS | Um ano; sem pressupor subdomínios/preload |
| Credenciais | 5 requisições/60 s/IP | Limitar repetição observada no Ex. 8 |
| Geral | 60 requisições/60 s/IP | Cota menos restritiva para as demais operações |

Valores são decisões de projeto; a exigência acadêmica é implementar os controles. `Settings` rejeita origens malformadas/wildcard e cota de credenciais igual/maior que a geral. Limites configuráveis por `LOGIN_RATE_LIMIT` e `GENERAL_RATE_LIMIT`.

## Ordem e comportamento

`app/network.py`: headers → CORS/preflight → rate limiting → JWT → validação/autorização/operação. Preflight permitido não exige token nem consome cota; origem/método/header proibido retorna 400. Requisição simples de origem negada pode receber 200 sem ACAO. CORS não dispensa JWT nem impede cliente HTTP direto.

Login humano, M2M e MFA compartilham a cota de credenciais. Janela móvel usa relógio monotônico e lock; excesso retorna 429, Retry-After e no-store antes de bcrypt/operação. Negativas 429 não prolongam janela. Chave usa endereço da conexão; executar Uvicorn direto com `--no-proxy-headers` evita confiar em encaminhamento enviado pelo cliente.

HSTS depende de HTTPS; não habilita TLS nem protege a primeira conexão HTTP. TestClient em HTTPS verifica header, não certificado/browser. Com proxy futuro, definir origem confiável e validar esquema/IP.

## Evidências e limites

- VUL-002/TM-012/TEST-15: DENY/nosniff em sucesso/erros; HSTS em HTTPS em processo, ausente em HTTP; CORS permitido/negado.
- VUL-003/TM-016/008/TEST-14: das mesmas 20 falhas de login, cinco 401 e demais 429; login conhecido permitido após a janela.
- [Ex. 10](../evidencias/ex10/README.md): 163 testes e 35 observações HTTP, incluindo status 200/400/401/403/404/422/429 e recuperação por relógio controlado.

Contador em memória é local a um processo: NAT compartilha cota; reinício/workers/IPs distribuídos limitam a proteção. Sem teste de capacidade ou TLS real. No capstone, CSP da agenda e no-store das respostas protegidas foram acrescentados; detalhes e riscos no [relatório final](relatorio-capstone.md).

Referências: [RFC 6797 HSTS](https://www.rfc-editor.org/rfc/rfc6797), [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/).
