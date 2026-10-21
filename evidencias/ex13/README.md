# Evidências — Exercício 13

## Execução passiva do ZAP

- Imagem oficial: `ghcr.io/zaproxy/zaproxy:stable`.
- Digest efetivamente usado: `sha256:5ccfff9a411743ab2615136a2edd7416bec9ce41572fa94e935df38c14adb2b6`.
- ZAP **2.17.0**, `mode=safe`, active scanners desabilitados, sem spider/active scan.
- Alvo `http://127.0.0.1:8001`; proxy/API ZAP `http://127.0.0.1:8090`.
- Banco/cadastro/credenciais efêmeros; MFA simulado, quotas 5/60; Secure=false somente neste HTTP local.
- 25 requisições por execução: raiz/schema/Swagger, login/MFA, CRUD, cookie/agenda, M2M e negativas de vínculo/papel/campo extra/finalidade.
- Não houve download/execução de JS do CDN pelo navegador nem verificação de TLS. XSS/SQL/ownership são complementados pelos testes existentes, não comprovados por um scan passivo.

Comandos executados (Docker precisa de acesso ao daemon; portas devem estar livres):

```bash
docker pull ghcr.io/zaproxy/zaproxy:stable
docker run --rm -d --name at-capstone-zap --network host \
  ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 127.0.0.1 -port 8090 \
  -config api.disablekey=true -config autoupdate.checkOnStart=false \
  -config autoupdate.installAddonUpdates=false -config autoupdate.downloadNewRelease=false
.venv/bin/python scripts/zap_passivo.py --output evidencias/ex13/zap-antes
# Após as correções da agenda e do contrato:
.venv/bin/python scripts/zap_passivo.py --output evidencias/ex13/zap-depois
```

Usar instância ZAP dedicada: o script cria uma nova sessão e recusa sobrescrever diretório de saída. Reprodução futura: mesmo digest, portas livres e saída nova em `reports/`. Comandos correspondem a Linux com network host; API sem chave apenas em loopback temporário.

| Artefato | Conteúdo |
| --- | --- |
| `zap-antes/`, `zap-depois/alertas.json` | Resposta real de alertas do ZAP, sanitizada para remover segredos efêmeros/JWT; 15 e 14 instâncias, respectivamente |
| `zap-antes/`, `zap-depois/zap.html` | Relatório HTML real, igualmente sanitizado |
| `trafego.json` em cada scan | Método, caminho, status esperado/observado e headers selecionados; não armazena corpos clínicos ou Authorization |
| `execucao.json` em cada scan | Versão, modo, alvo, fila passiva zerada e limites do experimento |
| `openapi.json` em cada scan | Contrato antes/depois; não contém credenciais |
| `uvicorn.log` em cada scan | Arranque/encerramento do servidor fictício, sem access log |
| `gate/` | Validação intermediária: 229 testes, seis LOW e SCA sem findings |
| `gate-final/` | Validação final: 233 testes, seis LOW, SCA sem findings e gate aprovado |
| `github-actions/` | Relatórios do run remoto aprovado no PR #17; [link, commit e resultados](github-actions.md) |

O exit 0 do script de tráfego significa conclusão do experimento e correspondência de status esperados, **não aprovação de segurança**. O alerta HIGH de transporte permanece e bloqueia deploy até TLS verificado. O gate CI existente não consome ZAP automaticamente; a decisão DAST faz parte da auditoria final.

Relatórios e decisão: [capstone](../../docs/relatorio-capstone.md), [auditoria OpenAPI](../../docs/auditoria-openapi.md).

## Gate final

Comando executado após os testes adicionais de login/scopes e organização do script:

```bash
.venv/bin/python scripts/security_gate.py --output evidencias/ex13/gate-final
```

Resultado: 233 passed, dois avisos de depreciação; Bandit com seis LOW (dois novos no executor de tráfego), SCA sem findings, gate aprovado. A triagem dos LOW e a decisão residual DAST estão no relatório final.

A instância foi encerrada com `docker stop at-capstone-zap`. O script reorganizado foi conferido em saída transitória, com 25 requisições/14 alertas. Após ajuste do formulário de login, os 19 testes de capstone passaram novamente.
