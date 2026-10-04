# Revisão documental — Exercício 3

## Origem e método

Baseline: `46db788b99a19b4cf145555e8e9ff679a88e29fe`; branch `feat/ex03-security-foundations-dfd`. Foram examinados os requisitos acadêmicos, a rubrica, a documentação técnica, os módulos `app/`, os testes e as evidências existentes. Esta revisão é inspeção de código/documentos e renderização do diagrama; não é scan nem novo teste de exploração.

## Resultado da inspeção

| Verificação | Resultado e localização |
| --- | --- |
| C, I e A têm ativos e consequências concretas | CIA-01–08 no relatório; confidencialidade de notas/atendimento, integridade de entrada/alteração e disponibilidade da memória/serviço |
| Cada componente tem correspondência no código | E-01/E-02 são consumidores dos contratos; P-01/P-02 rotas e apresentação; P-03 funções de dados; D-01 dicionário/contador |
| Todos os fluxos têm origem/destino e dados | F-01–10 em fonte Mermaid, diagrama e tabela; dez setas dirigidas |
| Criação JSON acompanha dados sensíveis | `ConsultaCreate` → `criar_consulta` → `_consultas` → `ConsultaResponse`; notas ficam armazenadas, mas são excluídas do JSON de sucesso |
| Leitura HTML acompanha dados sensíveis | `listar_consultas_do_dia` → projeção de cinco campos → Jinja2; motivo/notas não entram no contexto e status é escapado |
| Fronteiras não atribuem proteção inexistente | TB-01 exterior/processo; TB-02 divulgação interna lógica, mesmo processo; TB-03/04 futuras |
| Mapa OWASP está associado a controles reais | API3:2023 à redução de propriedades; A03:2021 ao escape; a relação é parcial e não comprova autorização/SQL parametrizado |
| NIST SSDF tem itens específicos | PW.5.1 à codificação segura, PW.8.2 aos testes/evidências e PW.1.2 aos registros de requisitos/decisões; escopo parcial |
| Referência MITRE é identificada | CWE 4.20: CWE-79/200/20 associados a escape, filtragem e validação; CWE-639 é candidato da lacuna, sem cenário autenticado já demonstrado |
| Dados fictícios e estado atual preservados | Sem credenciais, dados reais, JWT, banco ou laboratório implementados nos artefatos; seeds não consumidos pelas rotas |
| Limites de prova estão explícitos | Lock inspecionado, sem concorrência testada; filtragem de sucesso não comprova sanitização de erros; testes Ex. 2 reutilizados como histórico |
| Evolução tem IDs rastreáveis | AT-01–06, P-01–03, F-01–10, TB-01/02 e LAC-01–06; Threat IDs ficam para o STRIDE do Ex. 4 |

## Fontes oficiais consultadas

Os links para OWASP Top 10 2021, API Security Top 10 2023, NIST SP 800-218/SSDF 1.1 e páginas MITRE CWE estão na seção 5 do relatório. Foram conferidos o agrupamento de XSS em A03:2021, os itens PW.5.1/PW.8.2/PW.1.2 e as definições CWE citadas. A edição OWASP 2021 é uma escolha documentada, sem alegação de edição atual ou certificação.

## Pendências preservadas

Autorização por recurso, vínculo paciente/profissional, identidade M2M, validação estrita, tratamento de erros sensíveis, rate limiting, headers/CORS, persistência e regras de conflito continuam para seus incrementos correspondentes. O papel de paciente autenticado do Ex. 8 requer esclarecimento antes da implementação. Não há Threat Model STRIDE entregue nesta etapa.

## Verificação dos artefatos

Fonte Mermaid incorporada ao relatório e exportada com Mermaid 10.9.3. PNG e SVG devem corresponder à mesma fonte; o PNG foi inspecionado visualmente. O registro técnico e os hashes constam em `baseline.txt`; não demonstram testes além das verificações expressamente registradas.
