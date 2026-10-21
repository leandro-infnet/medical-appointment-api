# Evidências — Exercício 8

Revisão manual: A01 histórico, A05 e A07 no baseline Ex. 7, com 37 observações (3 históricas + 30 do baseline + 4 didáticas). [Localização, causa, impacto e tratamento](../../docs/vulnerabilidades.md).

Paciente autenticado aparece só no experimento isolado; a aplicação não tem portal/prontuário. Aceite acadêmico desse recorte histórico/didático pendente.

| Arquivo | Conteúdo / alcance |
| --- | --- |
| `manifesto.json` | Revisões exatas e SHA-256 de 41 fontes: 29 atuais e 12 históricas |
| `snapshots/atual/`, `snapshots/historico/` | Fontes literais `.txt`, incluindo módulos/templates necessários à reprodução; não são importadas pela API final |
| `historico.json` | Três observações no código real Ex. 2: lookup por ID e PATCH sem identidade retornam 200 |
| `atual.json` | Trinta observações no baseline Ex. 7: ownership atual bloqueia, 20 falhas de senha sem throttling, login conhecido 200, ausência de headers, extra ignorado e XSS escapado |
| `didatico.json` | Quatro leituras em experimento de dois pacientes autenticados: próprias/alheias 200; trocou somente ID mantendo o token |
| `rotas.json` | Inventário de 14 operações declaradas no OpenAPI; superfícies auxiliares constam do inventário manual do relatório |
| `execucao.txt`, `avisos.txt` | Saída efetiva da reprodução, inclusive avisos das dependências TestClient |
| `ambiente.json` | Versões usadas; sem credenciais, chaves ou bearer |
| `revisao.html` | Registro HTML das respostas reais, escapado para consultar sem executar os payloads |
| `resumo-evidencias.html`, `revisao.png` | Resumo dos resultados observados e captura real do Chromium; não é screenshot de exploit em browser conectado |
| `reproduzir.py` | Script exploratório separado de pytest, com processos, memória e credenciais efêmeros |

## Reprodução

```bash
.venv/bin/python evidencias/ex08/reproduzir.py \
  > evidencias/ex08/execucao.txt 2> evidencias/ex08/avisos.txt
```

O script verifica SHA-256 e materializa baselines em processos/diretórios temporários. Funciona com os snapshots no ZIP, sem Git ou acesso ao cadastro real. Os 41 arquivos são fontes literais, inclusive whitespace; nenhuma correção posterior foi aplicada neles. As observações não são testes pytest; a suíte normal não foi executada nesta etapa.

## Captura

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex08-chromium \
  --screenshot="$PWD/evidencias/ex08/revisao.png" --window-size=1300,1000 \
  "file://$PWD/evidencias/ex08/resumo-evidencias.html"
```

Resumo escapado dos JSON em Chromium local, sem sessão conectada; no-sandbox só para a captura fictícia. Não comprova clickjacking/interceptação ou quebra de senha. XSS estava escapado e extras não elevavam papel. Correções e CVSS nas etapas seguintes, sem alterar estes resultados.
