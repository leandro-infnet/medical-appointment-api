# Rastreabilidade verificada — Exercícios 1 e 2

Esta matriz registra o que já foi implementado e verificado. A matriz central do [guia](../GUIA_DESENVOLVIMENTO_AT.md) mantém também as etapas planejadas. Vincular Threat IDs após o threat model dos Exercícios 3 e 4, sem inventar análise já realizada.

| Requisito | Exercício | Implementação / arquivo | Teste | Threat ID | Evidência | Rubrica / risco residual |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-01: ambiente, módulos, CRUD e pytest | 1 | `app/main.py`, `app/routes/consultas.py`, `app/database/`, `pyproject.toml` | `tests/test_consultas.py`: oito casos | A vincular | `evidencias/ex01/` | R01; memória e ausência de autorização nesta fase |
| REQ-02.1: saída JSON sem campos internos | 2 | `ConsultaResponse` em `app/models/consultas.py`; quatro operações JSON em `app/routes/consultas.py` | TEST-02: `test_respostas_excluem_campos_internos_sem_apagar_armazenamento` | A vincular: exposição de dados | `evidencias/ex02/respostas_http.json`, `pytest_output.txt` | R02; dados clínicos JSON ainda dependem de autorização futura |
| REQ-02.2: justificar contrato de saída | 2 | `docs/decisoes.md`: DEC-13 | Inspeção do contrato e comparação armazenamento × resposta no TEST-02 | A vincular | Comparação histórica com `evidencias/ex01/uvicorn_respostas_rotas.txt` e resposta atual | R03; campos novos exigem revisão explícita do contrato |
| REQ-02.3: agenda diária e herança | 2 | `app/routes/agenda.py`, `app/templates/base.html`, `agenda.html`; regra temporal em `app/database/consultas.py` | TEST-03: testes de filtragem, ordem, vazio, data inválida, relógio e UTC em `tests/test_respostas_templates.py` | A vincular | `agenda_xss.html`, `agenda_vazia.html`, `agenda_xss.png`, `pytest_output.txt` | R04; fuso provisório DEC-14 e acesso sem autenticação até Ex. 6 |
| REQ-02.4: proteção de saída XSS | 2 | Environment com auto-escape; texto sem `safe`; projeção sem campos clínicos internos | TEST-03: `test_agenda_escapa_texto_malicioso_armazenado` com script e imagem/handler | A vincular: XSS persistido | `payloads.json`, `respostas_http.json`, HTML, screenshot e pytest | R04; não comprova segurança em contextos JS/CSS ou autorização |

**Verificação executada:** 16 testes passaram (oito da fundação, oito casos do Exercício 2), com dois avisos de depreciação das dependências do TestClient. Evidências HTTP em processo geradas com memória isolada; screenshot do HTML efetivamente renderizado pelo Chromium. Não foi executado ZAP, previsto no Capstone.
