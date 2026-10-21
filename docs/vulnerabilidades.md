# Revisão manual OWASP — Exercício 8

Revisão de três categorias do OWASP Top 10:2021: A01, A05 e A07. BOLA corresponde também a API1:2023, referencial separado. O inventário percorreu HTTP → identidade/política → recurso → armazenamento → JSON/Jinja2; localizações referem-se aos snapshots, não às linhas atuais.

## Baselines e alcance

- Histórico real: `4d6d7e342ac3b64e621a4c4d5a60018022e0433b` (Ex. 2, pré-autenticação).
- Baseline da revisão: `c68979a6242e8772627f03def1a8ea565e715dae` (Ex. 7).
- [Ex. 8](../evidencias/ex08/README.md): manifesto SHA-256 com 41 fontes, inventário de 14 operações, 37 observações em processos isolados. Sem scanner nesta etapa.
- Paciente autenticado/prontuário não existem na API. DEMO-001 usa dois pacientes em aplicação isolada; aceite acadêmico do recorte histórico/didático permanece pendente.

## VUL-001 — Autorização por objeto ausente no histórico

- **Localização/causa:** `routes/consultas.py` histórico, GET linhas 54–61 e PATCH 71–78; lookup em `database/consultas.py`. Recebe ID e retorna/altera registro sem principal ou comparação de proprietário.
- **Tentativa:** criar consultas fictícias de pacientes 1/2; variar apenas o ID no GET e fazer PATCH da segunda sem identidade.
- **Resultado/impacto:** três respostas 200 em `historico.json`, com leitura de motivo/vínculo e alteração indevida. Histórico não tinha paciente autenticado nem prontuário real.
- **Categoria:** A01:2021, relacionada a API1:2023 BOLA. IDs imprevisíveis não substituiriam autorização.
- **Correção:** desde Ex. 6, `auth/policies.py` combina papel, profissional e vínculo; Ex. 9 centraliza JWT. Leitura/PATCH/DELETE cruzados retornam 404; anônimo 401; dono permitido e estado intacto. TM-002/003, CTRL-01/02, TEST-07/08/09.

**DEMO-001:** `reproduzir.py`, função `didatico`, valida JWT mas resolve ID sem comparar paciente; quatro leituras próprias/alheias retornam 200. A contraparte Ex. 9 compara proprietário e retorna 404 no acesso alheio. Experimento fora de `app/main.py` e da suíte final; não conta como finding adicional da aplicação.

## VUL-002 — Headers de proteção ausentes

- **Localização/causa:** `main.py` do baseline, linhas 26–39, sem middleware de headers; agenda emitia apenas Cache-Control.
- **Tentativa/resultado:** GET da agenda autenticada → 200; consulta sem token → 401. X-Frame-Options, nosniff, HSTS e CSP ausentes nos registros de `atual.json`.
- **Impacto/categoria:** ausência de defesas de navegador, A05:2021. Sem exploração de iframe/sniffing/TLS; HSTS ausente em HTTP local isoladamente não demonstra falha de produção.
- **Correção:** Ex. 10 acrescentou DENY/nosniff, HSTS só HTTPS e CORS explícito; Ex. 13 acrescentou CSP agenda. Mesmas respostas/erros verificadas em `test_hardening.py`. TLS/browser reais pendentes. TM-012, CTRL-11, TEST-15.

## VUL-003 — Login sem throttling

- **Localização/causa:** `routes/auth.py` do baseline, login linhas 19–33, e composição sem limitador. Cinco erros de MFA limitavam um desafio, não a senha/login global.
- **Tentativa/resultado:** vinte senhas incorretas para conta fictícia → 401 sem 429/Retry-After; senha correta conhecida → 200 imediatamente. `atual.json` omite bearer.
- **Impacto/categoria:** permite adivinhação automatizada e trabalho bcrypt repetido, A07:2021. Sem senha descoberta, tomada de conta, capacidade ou DoS demonstrados.
- **Correção:** Ex. 10 definiu cinco requisições/min/IP no grupo login/M2M/MFA, 60 nas demais. Mesma sequência: primeiras cinco 401, demais 429; após janela, login permitido. `test_hardening.py` usa relógio controlado. TM-016/008, CTRL-07, TEST-14; NAT/workers/distribuição residuais.

## Outras observações

| ID | Observação | Tratamento |
| --- | --- | --- |
| OBS-001 | Campo extra papel ignorado no POST, sem promoção | Extra forbid no Ex. 9; 201 → 422 |
| OBS-002 | Script no status era armazenado, mas escapado | Allowlist rejeita entrada; legado segue escapado; sem XSS executado |
| OBS-003 | Memória sem SQL | SQL antes/depois só em DEMO-002; parametrização real entrou no Ex. 11 |
| OBS-004 | Sem reserva atômica de horário | Transação/concorrência SQLite no Ex. 11 |
| OBS-005 | Sem auditoria persistente/limite global | Cotas no Ex. 10; auditoria permanece aberta |
| OBS-006 | Form M2M ignorava papel extra, sem promoção | Form extra forbid no Ex. 9; 200 → 422 |

XSS e SQL Injection pertencem ambos a A03:2021 e não foram contados como categorias distintas. O endpoint M2M constava do inventário, mas não do finding de extras; a interpretação literal de “não citado” permanece pendente.

[Comparações antes/depois](correcoes-entrada-saida.md), [CVSS/impacto](devsecops.md) e [riscos finais](relatorio-capstone.md). VUL-001 foi mitigada no Ex. 6 e VUL-002/003 no Ex. 10, dentro do alcance testado. O histórico não foi reintroduzido nas rotas finais.

Referências: [A01:2021](https://owasp.org/Top10/2021/A01_2021-Broken_Access_Control/), [API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/), [A05:2021](https://owasp.org/Top10/2021/A05_2021-Security_Misconfiguration/), [A07:2021](https://owasp.org/Top10/2021/A07_2021-Identification_and_Authentication_Failures/).
