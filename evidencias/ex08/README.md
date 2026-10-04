# Evidências da revisão manual — Exercício 8

## Objetivo, classificação e pendência

A revisão do baseline Ex. 7 e do histórico identifica três categorias distintas em OWASP Top 10:2021: VUL-001/A01 histórico, VUL-002/A05 e VUL-003/A07 atuais. API1:2023 BOLA é referencial separado, ligado a A01. [Relatório completo](../../docs/vulnerabilidades.md) contém localização, causa, payload, resultado, impacto, correção proposta e regressão por finding.

O contexto de paciente autenticado não existe no domínio real atual. O responsável autorizou histórico real mais experimento didático isolado, sem adicionar portal/papel de paciente. **Aceitação acadêmica desse enquadramento continua pendente**, logo não declarar R13/R14 integralmente atendidos. O experimento não é um finding da aplicação.

## Artefatos e resultados reais

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

Total: **37 observações registradas**, não 37 testes pytest. Há controles positivos e negativos adicionais por assertions no script. A suíte final não foi modificada nem executada neste incremento documental; as evidências pytest anteriores permanecem históricas.

## Reprodução e preservação

```bash
.venv/bin/python evidencias/ex08/reproduzir.py \
  > evidencias/ex08/execucao.txt 2> evidencias/ex08/avisos.txt
```

Instalar previamente as dependências pelo README. O script confere SHA-256, materializa os dois baselines em diretórios temporários e executa cada um em subprocesso com importação separada. Não depende de objetos Git na reprodução, funciona também com os snapshots no ZIP e não muda o Working Directory/Git/Uvicorn. Os snapshots foram originalmente obtidos por `git show` e conservam os bytes de cada revisão, inclusive whitespace legado. O atributo Git de whitespace aplica-se somente à pasta de snapshots, não ao código final.

O baseline atual auditado tem cadastro temporário, chave/senha/código MFA aleatórios e bcrypt custo 12. Nenhum token, hash de credencial ou segredo entra nos JSON/HTML/logs. Não houve senha descoberta: o login positivo usa a senha fictícia conhecida do provisionamento. Todo dado clínico é fictício. O script restaura variáveis e limpa memória; o processo isolado não altera `.env` ou cadastro real.

O ensaio vulnerável de paciente vive na função `didatico`, é criado somente em processo de evidência e nunca é registrado em `app/main.py`. Não deve ser servido como aplicação final nem incorporado à suíte como comportamento esperado. O script preserva deliberadamente observações vulneráveis do baseline congelado para o antes/depois; futuras correções não devem reescrever essas respostas como se fossem o estado histórico.

Os JSON mantêm métodos/URLs/payloads relevantes sem Authorization. A requisição repetida de login usa `grant_type=password`, conta fictícia e senha errada fictícia; a senha correta e os bearers são gerados em execução e omitidos da saída. O cenário BOLA histórico é explicitamente sem autenticação. Os tokens de pacientes do experimento são validamente assinados em processo separado, com IDs fictícios.

## Evidência visual

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex08-chromium \
  --screenshot="$PWD/evidencias/ex08/revisao.png" --window-size=1300,1000 \
  "file://$PWD/evidencias/ex08/resumo-evidencias.html"
```

O PNG foi inspecionado. O resumo foi montado a partir dos JSON observados, com conteúdo escapado. Chromium renderizou arquivo local sem servidor conectado; não prova clickjacking, navegação autenticada ou interceptação. `--no-sandbox` foi empregado apenas no arquivo fictício local, não é configuração de navegação externa.

## Limites e próximas etapas

- Não foi usado scanner; a leitura manual localizou causas e a execução apenas confirmou comportamentos.
- HTTP em processo não comprova TLS, carga, browser, proxy, SQL ou exploração externa.
- Headers ausentes são configuração observada, não roubo de sessão demonstrado; HSTS depende de HTTPS.
- Vinte falhas sem espera não demonstram quebra de bcrypt ou volume ilimitado; o limite de login será definido no Ex. 10.
- XSS está escapado, campos extras não elevam papel e memória não executa SQL. Não declarar esses ataques como explorados.
- VUL-001 já foi mitigado no Ex. 6; VUL-002/VUL-003 continuam abertos para Ex. 10. Ex. 9 reutiliza contratos/payloads e esclarece as lacunas SQL/XSS. CVSS/gate/ZAP são futuros.
- O aceite acadêmico do experimento/histórico é pendente; a autorização do responsável para a demonstração não substitui esse aceite.

[DEC-20](../../docs/decisoes.md), [threat model 1.4](../../docs/threat-model.md) e [rastreabilidade](../../docs/rastreabilidade.md) preservam o vínculo entre requisito, finding, ameaça, controle, evidência e risco residual.
