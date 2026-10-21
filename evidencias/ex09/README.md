# Evidências — Exercício 9

132 testes aprovados. Reprodução: 16 observações HTTP atuais, quatro de pacientes isolados, duas M2M anteriores e duas posteriores, além de SQL isolado antes/depois/positivo. [Correções e limites](../../docs/correcoes-entrada-saida.md).

| Arquivo | Conteúdo |
| --- | --- |
| `pytest_output.txt`, `execucao.txt`, `avisos.txt` | Saídas da suíte/reprodução |
| `resultados.json` | Respostas e experimento SQL parametrizado |
| `m2m-antes.json` | Duas observações no snapshot real Ex. 8, SHA-256 verificado |
| `ambiente.json` | Versões de Python, SQLite e dependências |
| `agenda-legado.html`, `comparacao.html` | HTML escapado e comparação dos resultados |
| `reproduzir.py` | Cenários e controles positivos em processos temporários |

## Reprodução histórica

No baseline Ex. 9, com dados/credenciais efêmeros e dependências instaladas:

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python evidencias/ex09/reproduzir.py
```

Preservar saídas anteriores. Snapshots/manifesto do Ex. 8 permitem reprodução sem Git; resultados apenas copiados daquele exercício não são nova execução. `m2m-antes.json` é execução nova do snapshot real. Sem scanner, SQLModel ou navegador conectado nesta etapa.

Paciente e SQL são didáticos isolados; XSS já era escapado. Form M2M não era finding de extras, mas constava do inventário. Aceite acadêmico desses recortes pendente. Banco real/headers/cotas foram verificados nos Ex. 10/11.
