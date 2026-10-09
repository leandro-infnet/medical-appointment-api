# Evidências — Exercício 12

Pipeline em `.github/workflows/security.yml`, política executável em `scripts/security_gate.py`, justificativa SDLC/CVSS/negócio e matriz STRIDE em [devsecops.md](../../docs/devsecops.md).

| Artefato | Natureza / finalidade |
| --- | --- |
| `antes/pytest.log`, `pytest.xml` | Suíte real: 214 testes passaram; dois avisos de dependências |
| `antes/bandit.json`, `bandit.log` | SAST real de app/scripts, quatro findings LOW; triagem abaixo |
| `antes/sca.json`, `sca.log` | SCA real retornou 12 registros de advisories para pip 25.1.1; seis IDs únicos, sem inventar CVSS ou explorar pacotes |
| `antes/gate.json`, `gate_antes_output.txt` | Gate real **bloqueado**, exit 1; motivos vinculados aos seis IDs SCA |
| `depois/` e `gate_depois_output.txt` | Mesmos comandos após pip 26.2.1: gate aprovado (exit 0), 214 testes passaram, quatro LOW Bandit e nenhuma vulnerabilidade retornada pela SCA |
| `cvss.json` | Vetores históricos CVSS v3.1 calculados com cvss 3.6; premissas condicionais em devsecops.md |
| `ambiente.json` | Versões reais após atualização de pip; versão anterior registrada no próprio relatório SCA |
| `gate_*_avisos.txt` | stderr real do executor; pode estar vazio |

Comandos efetivamente executados:

```bash
.venv/bin/python scripts/security_gate.py --output evidencias/ex12/antes
.venv/bin/python -m pip install --upgrade 'pip>=26.2,<27'
.venv/bin/python scripts/security_gate.py --output evidencias/ex12/depois
```

Não executar esses comandos sobre os diretórios históricos para sobrescrever a evidência. Para nova execução, usar o padrão `reports/security/`, ignorado. O executor escreve logs/JUnit/JSON; stdout/stderr foram redirecionados para os arquivos nomeados acima. O pip foi atualizado para 26.2.1 e o workflow também exige atualização antes da instalação. Não foram alteradas dependências de runtime da aplicação para esconder findings.

## Triagem SAST

| Regra/local | Severidade / análise |
| --- | --- |
| B106, `app/auth/tokens.py`, valores human_access/m2m_access | LOW: são discriminadores públicos de finalidade JWT, não senha, hash ou chave. Não foram suprimidos |
| B404, import subprocess no runner | LOW: dependência necessária para executar ferramentas locais; import não prova execução insegura |
| B603, execução no runner | LOW: argv montado por comandos fixos, `sys.executable`, argumentos de relatório e cwd conhecidos; sem shell/interpolação de corpo HTTP. Caminho de output vem de uso administrativo local/CI, não endpoint |

Os quatro findings permanecem nos JSONs e são aceitáveis para a política definida; HIGH bloquearia independentemente da confiança. Isso não prova que Bandit cobre BOLA, quotas ou todas as falhas possíveis.

## Limites e evidências pendentes

Os diretórios `antes/` e `depois/` preservam execuções locais. A execução remota aprovada, o artefato baixado e as capturas de proteção da main estão em [github-actions.md](github-actions.md) e `github-actions/`. O relatório remoto registra 214 testes aprovados, quatro findings LOW do Bandit e nenhuma vulnerabilidade retornada pela SCA.

A proteção exige PR, branch atualizada e check `Security gate`, sem bypass por administradores. Permanece pendente somente a demonstração remota de um PR impedido de fazer merge com check reprovado; não confundir a aprovação mostrada nas imagens com esse cenário negativo.

YAML foi analisado localmente com PyYAML e conferidos gatilhos, permissão de leitura, comando do gate e upload `always()`/erro em ausência. Isso não valida infraestrutura hospedada do GitHub. Testes de política usam mocks/relatórios fictícios, identificados no código; são distintos dos scanners reais acima. DAST/ZAP passivo e auditoria final ficam no Ex. 13; IAST é proposta não executada. Nunca incluir `.env`, banco/cadastro real, credenciais ou bearer na entrega.
