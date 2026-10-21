# Correções de entrada e saída — Exercício 9

## Contratos

| Entrada | Controle efetivo | Positivo | Negativo | Arquivo |
| --- | --- | --- | --- | --- |
| POST consultas | `extra='forbid'`, IDs positivos, limites existentes de texto | Entrada permitida → 201 | `papel=administrador` → 422, nenhuma criação | `app/models/consultas.py` |
| PATCH consultas | `extra='forbid'`, atualizações somente dos quatro campos declarados | Motivo/notas/data/status permitidos → 200 | IDs, papel, auditoria ou outro extra → 422, estado intacto | Mesmo módulo |
| Status PATCH | `Literal` dos três estados, nulo explícito rejeitado | Três estados → 200 | Desconhecido, caixa diferente, vazio, script, nulo → 422 | `ConsultaUpdate` |
| Username no login | `fullmatch` de `[a-z0-9_]{1,64}` | Conta fictícia registrada → token | Acento, quebra de linha, espaço, operador SQL, >64 → 422 | `models/identidades.py`, `routes/auth.py` |
| Formulário Client Credentials | `M2MTokenInput.extra='forbid'`, somente grant_type/scope | Basic válido e grant correto → 200 | Papel, client_id/client_secret no corpo ou paciente → 422, sem token | `models/identidades.py`, `routes/auth.py` |
| Motivo e notas | Texto livre limitado, sem regex clínica arbitrária | Acentos, apóstrofo e pontuação preservados | Ausência/nulo/limites continuam conforme schema | `models/consultas.py` |

Campo omitido no PATCH conserva valor; null só apaga notas, sendo rejeitado em data/status/motivo. Regex do username é aplicada após leitura do formulário e não aparece automaticamente no schema OAuth. O formulário humano não proíbe todos os extras; JSON de consultas, MFA e formulário M2M são estritos. Texto clínico mantém acentos/aspas/pontuação e limites, com valores SQL parametrizados na persistência final.

## Identidade e ownership

`auth/middleware.py` valida JWT uma vez nos segmentos consultas, agenda, admin, sessão e disponibilidade; dependências consomem o principal em `request.state`. Login/MFA e emissão M2M usam seus próprios controles. O middleware não resolve ownership pela URL: `policies.py` verifica registro/vínculo antes da operação, inclusive na criação/lista. Cookie só autentica agenda GET; Authorization inválido não cai para cookie.

Ao incluir outro recurso protegido, incluir seu segmento e política. CORS externo atende preflight; dependências sem principal negam 401.

## Mesmo ataque antes/depois

| ID / cenário | ANTES preservado | Mesmo ataque | CORREÇÃO / defesa | DEPOIS verificado | Limite |
| --- | --- | --- | --- | --- | --- |
| VUL-001 | Snapshot histórico real: GET/PATCH por ID sem identidade → 200 | GET/PATCH `/consultas/1` sem token | Middleware JWT + políticas do Ex. 6 | 401; profissional diferente válido → 404; dono continua 200 | Autorização já existia desde Ex. 6; paciente só didático |
| OBS-001 | Baseline Ex. 8: POST com `papel=administrador` → 201, extra ignorado | Mesmo campo/payload | `ConsultaCreate.extra='forbid'` | 422, sem criar consulta | Não havia elevação de papel demonstrada |
| Endpoint adicional | PATCH não era o endpoint de OBS-001; schema também ignorava extras por padrão | PATCH com papel/IDs e motivo | `ConsultaUpdate.extra='forbid'` | 422 e estado inalterado | Histórico contém PATCH para BOLA; este é um padrão/achado diferente |
| OBS-006 / endpoint adicional | Snapshot real do baseline Ex. 8: `/auth/m2m/token` com Basic válido e extra `papel` → 200 | Mesmo formulário grant_type/papel e credenciais fictícias equivalentes | `M2MTokenInput.extra='forbid'` | 422; controle sem extra permanece 200 | Ignorar papel não elevava privilégio; endpoint constava no inventário, mas não em finding de extras |
| OBS-002 / TM-005 | Ex. 8: script no status → 200; HTML já escapado | `<script>alert(1)</script>` | Allowlist na entrada + auto-escape preexistente | PATCH → 422; legado inserido no teste → HTML com texto escapado | Não existiu XSS explorado no antes real |
| DEMO-001 | Dois pacientes autenticados no experimento Ex. 8: ID alheio → 200 | Mesmo token de cada paciente; somente ID trocado | Comparar paciente do recurso com claim autenticado, no experimento corrigido | Próprio → 200; alheio → 404 | Sem portal no produto; equivalência dos atores/claims, chaves efêmeras novas |
| DEMO-002 / TM-015 | SQL intencionalmente concatenado apenas no experimento | `1 OR 1=1` | `WHERE paciente_id = ?`, valores separados | Antes IDs 1/2; depois vazio; controle paciente 1 retorna somente ID 1 | Experimento Ex. 9; SQLModel real verificado no Ex. 11 |

A escolha adicional foi `/auth/m2m/token`, que compartilhava extras ignorados, mas não havia sido apontado como finding desse padrão. Todas as rotas estavam no inventário Ex. 8; a interpretação literal de “nunca citado” continua pendente. `m2m-antes.json` reproduz snapshot real com SHA-256 verificado; não havia elevação de papel.

## HTML, erros e SQL

Jinja2 mantém herança, projeção mínima e auto-escape sem safe. Allowlist impede novo script no status; o teste de legado verifica texto escapado/ausência de tags executáveis. Com CHECK no banco atual, o legado é projetado por mock, sem enfraquecer constraints.

`errors.py` responde 422 somente com loc/type/msg, sem input/contexto/corpo. Registros de erro não repetem os valores clínicos usados nos testes. SQLModel/SQLite do Ex. 11 usa parâmetros vinculados e rejeita operadores em IDs/filtros com 422.

## Verificação e ressalvas

Ex. 9: 132 testes; 16 observações HTTP atuais, quatro de paciente isolado, quatro M2M antes/depois e SQL isolado com controle positivo. Arquivos/comandos em [evidências](../evidencias/ex09/README.md). TEST-03/07/08/09/11/12/13/22 ligam TM-001/002/003/005/006/011/014/015 às regressões.

Paciente e SQL antes/depois são experimentos isolados; o produto não tinha SQL vulnerável nem XSS executado. Aceite acadêmico desses recortes permanece pendente. Hardening Ex. 10 mitigou VUL-002/003 e persistência Ex. 11 comprovou parametrização real, sem mudar a natureza dos experimentos. [Riscos finais](relatorio-capstone.md).
