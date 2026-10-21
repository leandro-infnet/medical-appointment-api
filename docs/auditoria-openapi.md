# Auditoria OpenAPI — Capstone

## Escopo e método

Comparação da especificação `/openapi.json` com rotas, modelos e respostas reais da aplicação. Snapshots antes/depois em `evidencias/ex13/zap-antes/openapi.json` e `zap-depois/openapi.json`; verificações automatizadas em `tests/test_capstone.py`, complementadas pelos testes integrados de autorização e validação existentes. Um security scheme declara o contrato, mas a aplicação do controle é comprovada pelos testes HTTP.

## Resultado por contrato

| Item | Observação / decisão | Verificação |
| --- | --- | --- |
| Consultas JSON | Bearer obrigatório, entrada extra proibida, saída sem notas internas/timestamps/hash | `test_openapi_contratos_de_entrada_saida_e_scopes`, suíte de consultas e respostas |
| Agenda HTML | Middleware aceita bearer OU cookie `agenda_session`; antes só bearer aparecia no OpenAPI | **OA-01 corrigido:** `AgendaCookie` declarado como alternativa, sem duplicar o validador JWT; `test_openapi_agenda_aceita_bearer_ou_cookie` |
| Erros de acesso | Agenda, diagnóstico administrativo e criação/exclusão da sessão retornavam 401/403 sem declarar essas respostas | **OA-02 corrigido:** decorators/routers documentam ambos; três casos parametrizados `test_openapi_documenta_erros_de_acesso_reais` |
| Identidade M2M | Basic na emissão, Client Credentials no fluxo e scope `disponibilidade:ler` no recurso; não é login humano | Schema e testes M2M de audiência, token_use, claims/scope e acesso cruzado |
| Login/MFA | Login público recebe formulário; administrador obtém 202 com desafio, não acesso completo. MFA recebe corpo com extra proibido | Testes administrativos/MFA e tráfego ZAP; união de saída 200 ainda é mais ampla que a resposta real de sucesso comum, mas 202 está declarado |
| Validação de erro | Handler retorna somente loc/type/msg, não input/contexto clínico | `test_tm006_tm011_erro_nao_grava_nem_repete_campo_extra` e suíte de entrada/saída |
| PATCH omitido versus null | Omitir mantém campo; null em horário/status/motivo é rejeitado pelo validador. O schema opcional ainda admite null nesses campos | **OA-03 limitação documentada:** cliente deve omitir campo não alterado, em vez de enviar null. Regressões de entrada verificam 422 real; não é bypass de validação |
| Escopo do contrato | Segurança dos modelos de entrada não define ownership, papéis, vínculos nem todas as regras temporais | Testes de política e banco verificam restrições além do OpenAPI |
| Respostas de banco | 409 para sobreposição em criação/alteração; 503 para indisponibilidade de escrita; não revelam SQL | Suíte de persistência e respostas declaradas nas consultas |

## Evidência antes/depois

A execução inicial de `pytest tests/test_capstone.py -q` retornou **10 passed, 3 failed**: os três casos de erros de acesso falharam por ausência de `401` no schema. Após corrigir a documentação e acrescentar cookie/CSP/cache, `pytest tests/test_capstone.py tests/test_hardening.py -q` retornou **46 passed**. Esses números são resumos das execuções locais, não arquivos de stdout bruto preservados. A suíte completa final tem saída/JUnit próprios em `evidencias/ex13/gate/`.

OA-01/OA-02 são lacunas de contrato, não demonstrações de acesso indevido. OA-03 permanece diferença de representação a considerar nos clientes. Não foram alegados vazamento, bypass ou execução de ataque onde somente revisão de schema foi realizada.
