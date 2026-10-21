# Decisões técnicas

Registro das escolhas e alternativas. Os IDs originais são mantidos; detalhes de execução e resultados ficam nos relatórios/evidências de cada exercício.

## DEC-01 — Módulos

Separar HTTP, modelos, dados, autenticação e templates. Concentrar tudo em `main.py` dificultaria revisão e evolução; o ponto de entrada fica com a composição. Não houve necessidade de microserviços ou repositórios genéricos.

## DEC-02 — Contrato REST

POST cria (201), GET lista/busca (200/404), PATCH altera parcialmente (200/404), DELETE remove fisicamente (204/404). Cancelamento usa PATCH de status. Campos internos permanecem separados da saída pública desde DEC-13.

## DEC-03 — Vínculo paciente/profissional

Manter IDs explícitos na consulta, mas verificar relação confiável no servidor. Seeds iniciais eram apenas referências; o Ex. 6 acrescentou ownership e o Ex. 11 FK. Nenhum ID recebido comprova identidade.

## DEC-04 — Memória e banco final

Memória permitiu a fundação inicial; funções de acesso separadas limitaram o impacto da migração. DEC-23 adotou SQLite/SQLModel no Ex. 11. Banco de outro motor exigiria revisão das garantias de concorrência.

## DEC-06 — Ambiente e configuração

Ambiente virtual, `pyproject.toml` e BaseSettings/.env. Segredos ausentes impedem arranque seguro. Sem lockfile; os relatórios guardam versões observadas e não garantem instalação idêntica futura.

## DEC-13 — Saída mínima

`ConsultaResponse` declara seis campos, excluindo notas/timestamps internos. Repetir exclusões em cada rota facilitaria divergência; allowlist própria preserva o contrato quando a tabela cresce. Agenda recebe apenas IDs, horário e status, usa herança Jinja2 e auto-escape. Evidência: Ex. 2 e testes de resposta/HTML.

## DEC-14 — Dia e fuso

Fuso único `America/Sao_Paulo`, inicialmente provisório e mantido na disponibilidade. Horário sem offset é local; com offset, converter antes do filtro diário. Evita depender do fuso do servidor. Não há configuração por clínica ou política de feriados.

## DEC-15 — Referenciais

Fixar OWASP Top 10:2021, API Security Top 10:2023, NIST SSDF 1.1/SP 800-218 e MITRE CWE 4.20 para manter comparação entre etapas. São escolhas de edição, sem alegação de versão mais recente ou certificação. [Mapa aplicado](cia-dfd.md).

## DEC-16 — STRIDE

Analisar S/T/R/I/D/E em P-01 JSON, P-02 HTML e P-03 dados; conservar IDs de ativos/fluxos/ameaças. A lista genérica de ameaças foi evitada porque não localizaria causa, controle e teste. [Snapshot inicial](../evidencias/ex04/threat-model-v1.md) e [modelo atual](threat-model.md).

## DEC-17 — Partições e controles

Identidade compartilhada valida token; política decide papel, vínculo e recurso. Colocar todo ownership no middleware perderia contexto, e copiar regras em rotas duplicaria lógica. [Arquitetura](arquitetura-seguranca.md) localiza doze vetores nos três eixos.

## DEC-18 — Identidade humana e agenda

RBAC mais vínculo/ownership; diagnóstico admin sem clínica; bcrypt custo 12; JWT HS256 de 15 min; MFA simulado com desafio de 300 s/cinco erros. Cookie HttpOnly/Secure/SameSite Strict, path `/agenda`, só para GET HTML. Bearer exclusivo em navegador comum exigiria cliente especial; token em URL exporia credencial. Cadastro/desafio locais e ausência de revogação individual limitam uso em produção. [Contrato](autenticacao-autorizacao.md).

## DEC-19 — Laboratório e disponibilidade

Client Credentials autentica o parceiro em nome próprio, com audiência/finalidade e scope mínimos. Authorization Code seria delegação humana; senha de profissional misturaria identidades. Escolha de domínio: 30 min, dias úteis 08h–18h, fuso da clínica; cancelada libera. Disponibilidade é leitura, sem reserva. [Contrato M2M](integracao-m2m.md).

## DEC-20 — BOLA histórica e paciente didático

Revisar código real histórico/atual e demonstrar paciente autenticado em aplicação isolada, sem portal no produto. A01 histórico, A05 e A07 do baseline compõem três categorias distintas. SQL inexistente e XSS escapado não foram classificados como explorações. Aceite acadêmico do recorte histórico/didático pendente. Snapshots de código com SHA-256 ficam no Ex. 8. [Revisão](vulnerabilidades.md).

## DEC-21 — Contratos estritos e middleware

Middleware ASGI valida identidade uma vez; políticas mantêm ownership. Adotar extra forbid, status agendada/cancelada/realizada e regex ASCII para username, preservando texto clínico livre limitado. Form M2M também rejeita extras, mantendo scope omitido/vazio distintos. Endpoint já constava no inventário, embora não no finding desse padrão: interpretação literal permanece pendente. SQL antes/depois foi isolado em SQLite no Ex. 9; SQLModel entrou depois. [Comparações](correcoes-entrada-saida.md).

## DEC-22 — Hardening local

CORS de demonstração explícito, DENY/nosniff e HSTS só HTTPS. Cotas: cinco requisições/min/IP para login/M2M/MFA e 60 nas demais. Escolha simples para um processo, sem serviço externo de contagem; NAT/workers/distribuição permanecem limites. Endereço vem da conexão; execução direta usa `--no-proxy-headers`. [Hardening](hardening.md).

## DEC-23 — SQLModel/SQLite e sobreposição

Arquivo local simplifica entrega; PostgreSQL não era necessário. Modelos internos separados dos contratos, sessões injetadas, PK/FK/CHECK e UTC. Sobreposição de 30 min por profissional gera 409, inclusive em atualização/reativação; cancelada libera, adjacência permite. `BEGIN IMMEDIATE` precede leitura de ownership/conflito; rollback em falha; BUSY/LOCKED após timeout gera 503. Escrita externa pode contornar a regra. `create_all` não migra schema; recuperação operacional pendente. [Persistência](persistencia.md).

## DEC-24 — Pipeline e critério de bloqueio

GitHub Actions executa pytest, Bandit e pip-audit. Bloquear falha/skip, HIGH nativo, advisory não triado e análise incompleta; preservar relatórios. Histórico BOLA/login/headers exige regressões de negócio além dos scanners. HIGH não é conversão de CVSS; scores 9,1/0,0 provisório/7,4 têm premissas e impacto em [DevSecOps](devsecops.md). Check obrigatório da main e PR #15 demonstram bloqueio. DAST entra na auditoria final; IAST é proposta instrumentada, não execução.

## DEC-25 — Capstone e liberação

ZAP passivo em loopback com dados fictícios, testes com mocking e auditoria OpenAPI. Corrigir CSP agenda, no-store, erros documentados e cookie como alternativa bearer; manter alertas na triagem. **Produção bloqueada** por transporte, identidade simulada, auditoria e recuperação pendentes. Swagger externo sem CSP/SRI continua limitado ao uso local. [Relatório final](relatorio-capstone.md).
