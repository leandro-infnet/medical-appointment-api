# Evidências — Exercício 10

## Reprodução

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python evidencias/ex10/reproduzir.py
```

Executar na raiz com dependências instaladas. Dados fictícios, cadastro temporário, senha/chave/MFA aleatórios. O script omite bodies de token e headers de autenticação; só registra status e headers públicos. Nenhuma credencial real deve entrar no pacote.

| Arquivo | Evidência |
| --- | --- |
| `pytest_output.txt` | 163 testes passaram; dois avisos de dependências |
| `execucao.txt`, `avisos.txt` | Saída e avisos reais do script |
| `respostas_http.json` | 35 observações: HTTPS em processo, HTTP local, CORS, 20 senhas inválidas, cotas e recuperação |
| `hardening.html` | Exibição escapada dos resultados estruturados |
| `ambiente.json` | Python e versões das bibliotecas |
| `reproduzir.py` | Cenários, assertions e controles positivos |

As 60 respostas positivas da cota geral foram verificadas antes do 429; são resumidas no cenário correspondente e não 60 testes pytest adicionais. Relógio controlado dispensa esperar um minuto. O estado é reiniciado somente entre cenários/arranques, nunca entre tentativas da mesma sequência de abuso.

Antes: `../ex08/atual.json` registra ausência de headers e 20 tentativas inválidas sem throttling no baseline congelado. Depois: este script verifica bloqueio com a mesma sequência de tentativas e conta profissional fictícia equivalente; não afirma descoberta de senha.

**Limitações:** HTTPS do TestClient não comprova handshake TLS ou aplicação de HSTS pelo navegador. CORS/headers foram verificados por HTTP em processo, sem screenshot de browser. Contador em memória, processo único, sem teste de carga, ZAP ou deploy. Os scripts/evidências antigos permanecem históricos; não reexecutá-los para sobrescrever os resultados anteriores com o contrato atual.

[Configuração e decisões](../../docs/hardening.md) e [rastreabilidade](../../docs/rastreabilidade.md) relacionam R17, TM-012/016/008 e TEST-14/15.
