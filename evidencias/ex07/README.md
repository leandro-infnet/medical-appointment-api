# Evidências do Exercício 7

Baseline: `ec391e97f9afdc508429fb3a20ce33399e8bbb2f`, merge do Ex. 6. Objetivo R12: justificar/implementar fluxo OAuth 2.0 adequado e scopes/claims que separem acesso humano e M2M. Client Credentials foi selecionado; a regra de disponibilidade foi aprovada pelo responsável pelo projeto.

## Artefatos reais

| Artefato | Origem / alcance |
| --- | --- |
| `pytest_output.txt` | `.venv/bin/python -m pytest tests/ -v`: **101 passed**, dois avisos; 60 regressões anteriores + 41 casos M2M |
| `respostas_http.json` | 20 cenários HTTP em processo, com código/status/body e sem segredos ou bearer |
| `claims_publicas.json` | Contrato do JWT realmente emitido: subject/audiência/emissor/finalidade/client ID/scope; sem token bruto ou dados clínicos |
| `ambiente.json` | Python e versões efetivamente usadas na reprodução |
| `dfd-atual.svg`, `dfd-atual.png` | Fonte `docs/dfd-atual.mmd` renderizada em Mermaid 10.9.3/Chromium; parceiro, P-06/TB-03 e F-26–33 |
| `reproduzir.py` | Reprodução isolada que preserva/restaura ambiente e não usa cadastro/credencial existentes |

A evidência demonstra token M2M válido lendo apenas disponibilidade, Basic/grant/scope inválidos rejeitados, token humano negado na rota do laboratório e M2M negado em oito operações humanas, sem alteração da consulta fictícia. Scope vazio obtém token sem permissão e recebe 403. Fim de semana não abre expediente, profissionais são separados e cancelamento libera os slots. Os testes adicionais cobrem assinatura/algoritmo/claims/expiração, cliente desativado, sobreposição com hora fora do grid, UTC e contrato OpenAPI.

## Comandos de reprodução

```bash
.venv/bin/python -m pytest tests/ -v > evidencias/ex07/pytest_output.txt
.venv/bin/python evidencias/ex07/reproduzir.py
```

O script gera credencial/chave aleatórias, hashes bcrypt custo 12 e cadastro humano temporário em processo próprio. Não edita `.env`, não provisiona laboratório no ambiente do usuário e não toca no Uvicorn existente. Fixtures de testes usam custo 4 somente para testes. Credenciais reais, hash local, bearer e ambiente virtual não entram no Git/ZIP.

Para reproduzir a exportação, usar a fonte Mermaid em HTML local com `securityLevel: strict`, `startOnLoad: true`, biblioteca Mermaid 10.9.3, Chromium headless, orçamento virtual de dez segundos e viewport 2400×900. O DOM renderizado foi verificado sem erro de sintaxe e o SVG extraído; PNG foi inspecionado visualmente. HTML/biblioteca temporários ficaram em `.local/ex07-render`, fora da entrega. `--no-sandbox` serviu apenas a fonte local fictícia, não configura navegação externa segura. A API não depende de Chromium/Mermaid.

## Ajustes encontrados durante verificação

- O teste de Basic malformado inicialmente usou header com acento, recusado pelo próprio cliente HTTP. Corrigido para header ASCII malformado; a negação passa pela aplicação.
- A reprodução detectou que `Form` transforma campo vazio em default. A emissão agora verifica se scope estava presente; vazio mantém permissão vazia, omissão concede apenas o padrão mínimo. Teste verifica o scope da resposta emitida, além de testar autorização do recurso.
- HTTP Basic preserva a descrição no OpenAPI e retorna erros OAuth com `error` no nível superior. Grant ausente segue 422 do FastAPI, documentado no contrato.

## Limites e continuidade

HTTP foi exercitado com TestClient; não prova TLS, capacidade, rede externa, integração com laboratório real ou navegador conectado. Não houve ZAP, SQLModel, gate ou deploy. Dois avisos de depreciação do TestClient/httpx e alias AnyIO permanecem; SonarLint/Pylance não foram executados via CLI.

Disponibilidade é consulta de snapshot, não reserva atômica. O CRUD não ganhou garantia contra sobreposição; estados desconhecidos bloqueiam conservadoramente. Hash ausente desativa M2M; trocar somente hash não revoga tokens existentes. Bearer roubado conserva acesso somente ao contrato autorizado até expiração/desativação; rate limiting e TLS permanecem pendentes.

[Contrato técnico](../../docs/integracao-m2m.md), DEC-19, [threat model 1.3](../../docs/threat-model.md) e [rastreabilidade](../../docs/rastreabilidade.md) registram implementação/testes/evidências/riscos. Evidências anteriores foram preservadas. Não há autorização de liberação externa.
