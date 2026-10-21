# Auditoria OpenAPI

Comparação de `/openapi.json`, código e respostas reais. Snapshots em `evidencias/ex13/zap-antes/openapi.json` e `zap-depois/openapi.json`; testes em `tests/test_capstone.py`, junto às regressões HTTP existentes.

| Item | Resultado / verificação |
| --- | --- |
| Consultas | Bearer, extra forbid e saída sem campos internos; teste de contratos/scopes e suíte de respostas |
| OA-01: agenda | Cookie aceito no middleware, antes omitido no schema. Corrigido: AgendaCookie OU bearer; teste específico |
| OA-02: erros de acesso | 401/403 omitidos em agenda/admin/sessão. Corrigidos nos routers; três casos parametrizados verificam schema e 401 real |
| M2M | Basic na emissão, Client Credentials e scope disponibilidade:ler; testes de claims/audiência/acesso cruzado |
| Login/MFA | Login público, desafio admin 202 e MFA extra forbid. Schema de 200 ainda tem união mais ampla que a resposta comum; 202 está declarado |
| Erro de entrada | Handler devolve loc/type/msg, sem input/contexto; teste STRIDE de campo extra sem eco/gravação |
| OA-03: PATCH | Omitir mantém campo; null em data/status/motivo gera 422, embora schema opcional admita null. Limitação documentada: omitir campo não alterado |
| Banco | 409 de conflito e 503 de escrita indisponível documentados/verificados |

O schema não comprova ownership ou segurança efetiva: políticas, banco e HTTP são testados separadamente. OA-01/OA-02 são lacunas de contrato, sem bypass demonstrado.

Execução inicial: 10 testes passaram e três falharam por 401 ausente no schema. Após correção, capstone+hardening: 46 passaram. São resumos de execução local; o stdout dessas duas etapas não foi preservado. [Gate final](../evidencias/ex13/gate-final/pytest.log): 233 testes aprovados. Após ajustes de tipagem/preparação, os 19 testes de capstone passaram novamente.
