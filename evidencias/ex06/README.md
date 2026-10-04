# Evidências do Exercício 6

## Requisitos, resultado e baseline

Incremento sobre `fb75b016ed9e535fbb4bf1715af2b8a91f697bdf` (merge do Ex. 5). R10: OAuth2PasswordBearer, bcrypt e ownership. R11: JWT expirável, MFA simulado e modelo de autorização justificado. O teste exigido que nega administrador a quem não tem esse papel está em `test_nao_administrador_negado_na_rota_administrativa`, com profissional e recepção. É a base para expansão no Ex. 12.

A matriz e o transporte HTML foram aprovados pelo responsável pelo projeto. [Contrato técnico](../../docs/autenticacao-autorizacao.md), DEC-18, [threat model 1.2](../../docs/threat-model.md) e [matriz central](../../docs/rastreabilidade.md) descrevem decisões e riscos.

## Artefatos produzidos

| Arquivo | Origem e alcance |
| --- | --- |
| `pytest_output.txt` | Saída completa de `.venv/bin/python -m pytest tests/ -v`: **60 passed**, dois avisos de dependências, sem testes pulados |
| `respostas_http.json` | 21 cenários HTTP efetivamente executados por `reproduzir.py`; senha/token/hash/desafio/fator omitidos |
| `ambiente.json` | Versões efetivamente instaladas no processo de reprodução |
| `agenda_autenticada.html` | HTML obtido por GET com cookie da recepção; espaços finais normalizados; contexto mínimo, dados fictícios |
| `agenda_autenticada.png` | Renderização pelo Chromium do HTML salvo; não é teste de login/navegação no navegador conectado à API |
| `dfd-atual.svg`, `dfd-atual.png` | Renderização local Mermaid 10.9.3 da fonte atual, com identidade/políticas/cadastro/desafios; fonte em `docs/dfd-atual.mmd` |

A suíte contém 16 casos de regressão dos Ex. 1/2 adaptados para login real e 44 casos do Ex. 6. Verifica caminho autorizado, token ausente/inválido/expirado, algoritmo/claims, login inválido, UTF-8/bcrypt, MFA/fator/replay/tentativas, CRUD cruzado sem mutação, listagem, vínculo confiável, papel da recepção, flags/expiração/logout de cookie, conta desativada, configuração sem chave e cadastro sem sobrescrita.

Demonstração HTTP: anônimo 401; profissional legítimo cria 201; não admin recebe 403; outro profissional recebe 404 no alvo e lista vazia; criação sem vínculo recebe 403; admin recebe 202 sem bearer antes de MFA, fator incorreto 401, fator válido gera token, diagnóstico retorna 200 sem clínica; replay 401; recepção obtém cookie, abre agenda, cookie não autoriza JSON e logout encerra acesso do navegador.

## Reprodução

```bash
.venv/bin/python -m pytest tests/ -v > evidencias/ex06/pytest_output.txt
.venv/bin/python evidencias/ex06/reproduzir.py
```

O script usa `TemporaryDirectory`, senhas/código/chave aleatórios e hashes bcrypt, cria cadastro efêmero, substitui/restaura variáveis do processo e limpa memória. Não consulta nem altera `.env`, cadastro local existente ou servidor Uvicorn em execução. Não salva segredos nos artefatos. Dados de saúde são fictícios. Custo bcrypt 12 na reprodução; custo 4 apenas nos fixtures de testes.

Para capturar o HTML salvo:

```bash
chromium --headless --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/at-ex06-agenda-chromium \
  --screenshot="$PWD/evidencias/ex06/agenda_autenticada.png" --window-size=1100,800 \
  "file://$PWD/evidencias/ex06/agenda_autenticada.html"
```

A renderização do DFD usou HTML local temporário com Mermaid 10.9.3, `securityLevel: strict`, orçamento virtual de dez segundos, DOM exportado e extração do SVG. O HTML precisou ficar em diretório local do projeto porque o Chromium Snap não enxergou o arquivo em `/tmp`; a primeira tentativa não produziu imagem. Não houve alteração nas dependências Python para renderizar Mermaid. `--no-sandbox` foi usado somente para conteúdo local fictício, não é configuração de produção.

## Limites e riscos residuais

- Evidência HTTP é `TestClient` em processo; não prova TLS, rede, capacidade ou banco real.
- Flags do cookie são verificadas e cookie Secure não acompanha HTTP no cliente; não houve teste real cross-site/CSRF ou login conectado em browser. Cookie só autentica agenda GET; operações de sessão exigem bearer.
- MFA é código estático configurado localmente, sem canal/dispositivo independente; desafios de uso único são locais a um worker. Não é MFA de produção; novo login pode renovar tentativas.
- Logout apaga cookie, sem revogar JWT roubado; tokens expiram e contas desativadas são recusadas. Cadastro em arquivo é carregado no startup.
- Middleware JWT, rate limiting, headers/CORS, SQLModel, M2M e ZAP continuam previstos nas próximas etapas.
- Pytest emitiu os avisos de depreciação Starlette/httpx e alias AnyIO, sem falhas.
- Nenhuma credencial real, `.env`, hash de conta local, dado pessoal real ou ambiente virtual deve entrar no repositório/ZIP. Não há liberação de deploy.

## Revisão de documentação HTTP e diagnósticos estáticos

Após os ajustes de OpenAPI e legibilidade, foram executados `pytest tests/test_autorizacao.py tests/test_consultas.py -q` (52 casos passaram; dois avisos das dependências) e novamente os 21 cenários de `reproduzir.py`. Os oito casos de templates não foram repetidos nessa revisão; a saída completa de 60 casos acima pertence à validação anterior. O schema OpenAPI gerado foi inspecionado: GET/PATCH/DELETE por ID documentam 401/403/404 e MFA documenta 401.

Pylance e SonarLint não foram executados via linha de comando nesta revisão. As três chamadas a BaseSettings têm supressão localizada de `reportCallIssue`, pois a assinatura sintetizada pelo analisador não representa a leitura de campos obrigatórios pelo ambiente nem `_env_file`. Não foram adicionados defaults secretos ou desativadas regras globalmente; os testes de ausência de chave e de erro sem exposição continuam passando.
