# Evidências — Exercício 7

Baseline: `ec391e97f9afdc508429fb3a20ce33399e8bbb2f`. R12: Client Credentials, claims/scopes e leitura mínima de disponibilidade. [Contrato](../../docs/integracao-m2m.md).

| Artefato | Origem / alcance |
| --- | --- |
| `pytest_output.txt` | `.venv/bin/python -m pytest tests/ -v`: **101 passed**, dois avisos; 60 regressões anteriores + 41 casos M2M |
| `respostas_http.json` | 20 cenários HTTP em processo, com código/status/body e sem segredos ou bearer |
| `claims_publicas.json` | Contrato do JWT realmente emitido: subject/audiência/emissor/finalidade/client ID/scope; sem token bruto ou dados clínicos |
| `ambiente.json` | Python e versões efetivamente usadas na reprodução |
| `dfd-atual.svg`, `dfd-atual.png` | Fonte `docs/dfd-atual.mmd` renderizada em Mermaid 10.9.3/Chromium; parceiro, P-06/TB-03 e F-26–33 |
| `reproduzir.py` | Reprodução isolada que preserva/restaura ambiente e não usa cadastro/credencial existentes |

101 testes (60 anteriores + 41 M2M); 20 cenários HTTP. Token do parceiro lê disponibilidade e é negado nas oito operações humanas; token humano é negado no parceiro. Scope vazio continua sem permissão; omissão concede apenas o mínimo. A reprodução identificou coerção Form de vazio para default, corrigida pela verificação de presença do campo.

## Reprodução histórica

No baseline Ex. 7, com cadastro/segredos temporários; preservar saídas anteriores:

```bash
.venv/bin/python -m pytest tests/ -v > evidencias/ex07/pytest_output.txt
.venv/bin/python evidencias/ex07/reproduzir.py
```

DFD exportado com Mermaid 10.9.3 e Chromium, viewport 2400×900, orçamento virtual 10 s, fonte local. TestClient e imagem não comprovam TLS/browser/laboratório real. Disponibilidade não reservava horário; conflito passou a ser impedido na escrita no Ex. 11. Revogação individual e TLS real permanecem limites.
