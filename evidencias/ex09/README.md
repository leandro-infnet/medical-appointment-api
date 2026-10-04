# Evidências — Exercício 9

Dados exclusivamente fictícios. A execução usa contas temporárias, bcrypt, chave JWT/senha/MFA aleatórios e tokens omitidos. Não carregar ou distribuir `.env`, cadastro local de contas ou credenciais reais no ZIP.

## Reprodução

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python evidencias/ex09/reproduzir.py
```

Executar na raiz com dependências instaladas. `TestClient` chama a aplicação em processo; não há requisições a serviço público. O script cria SQLite `:memory:` somente no experimento DEMO-002 e uma segunda FastAPI local somente na contraparte corrigida de DEMO-001. Nenhum deles integra a aplicação ou a descoberta pytest.

Validação executada: **132 testes passando**, dois avisos de depreciação de dependências. Reprodução passou: 16 observações HTTP atuais, quatro de pacientes isolados, duas M2M anteriores e duas posteriores; SQL isolado com ataque antes/depois e controle positivo. Essas observações não são 24 testes pytest adicionais.

| Arquivo | Conteúdo |
| --- | --- |
| `pytest_output.txt` | Saída real da suíte integrada, incluindo avisos |
| `execucao.txt`, `avisos.txt` | Saída/avisos da reprodução |
| `resultados.json` | 16 observações HTTP atuais, quatro de paciente isolado, quatro M2M antes/depois e SQL antes/depois/positivo |
| `m2m-antes.json` | Duas observações reais em snapshot Ex. 8: positivo e extra ignorado; SHA-256 verificado |
| `ambiente.json` | Python, SQLite e versões das dependências |
| `agenda-legado.html` | HTML real renderizado com payload legado escapado; espaços finais de linha removidos para versionamento |
| `comparacao.html` | Exibição escapada de resultados e fontes anteriores |
| `reproduzir.py` | Código do experimento, assertions e controles positivos |

Os resultados do Ex. 8 copiados para comparação são **evidências anteriores**, não novas execuções no Ex. 9. A exceção é `m2m-antes.json`, nova execução do baseline real materializado a partir dos snapshots com hashes verificados. Os snapshots e manifesto continuam intactos em `../ex08/`; nenhum Git é necessário para reproduzir no ZIP. O script Ex. 8 conserva baselines congelados; o script Ex. 9 verifica o código atual e evoluirá somente com mudanças explicitamente documentadas. Não interpretar resultados deliberadamente vulneráveis dos experimentos como gate da API atual.

Não há screenshot novo, execução em navegador, scanner, SQLModel ou deploy nesta etapa. O HTML evidencia caracteres escapados; o parsing de tags é verificado em pytest, não execução de JavaScript no navegador.

## Limitações de conclusão

SQL e paciente são didáticos isolados, com aceite acadêmico pendente. XSS real já escapava no baseline anterior. M2M foi aprovado como endpoint adicional não citado como finding de extras; todos os endpoints constavam no inventário, deixando pendente a leitura literal de nunca citado. Headers/throttling permanecem para Ex. 10; integração SQLModel para Ex. 11. A [análise de correções](../../docs/correcoes-entrada-saida.md) preserva essas distinções e o mapa R14–R16.
