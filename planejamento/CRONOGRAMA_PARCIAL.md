# Entrega parcial — domingo, 13/09/2026

Plano proposto para uma versão demonstrável do software e uma versão parcial coerente do TCC. Não representa funcionalidades já implementadas. Data final e critérios institucionais ainda pendentes.

## O que deve estar pronto

Software: importar um CSV documentado, validar linhas, persistir dados, apresentar indicadores e listar oportunidades com filtros. Um experimento de priorização deve ser reproduzível e explicitar seus limites; a integração de ML na interface depende da auditoria e da conclusão desse experimento.

Texto: introdução, problema, justificativa, objetivos, delimitação, fundamentação com referências verificadas, metodologia e desenvolvimento das partes realmente implementadas. Resultados preliminares apenas quando medidos. Avaliação final, discussão completa e conclusão ficam pendentes, identificadas como tal.

Os 50–60% e 70% pedidos serão tratados como metas aproximadas. O aceite usa as entregas abaixo, e não quantidade de páginas ou código.

## Sequência de trabalho

| Data | Software e dados | Texto e evidências |
| --- | --- | --- |
| 07–08/09 | Obter e auditar base; decidir campos, alvo e limites; verificar ambiente | Consolidar problema, objetivos, escopo e protocolo de avaliação |
| 09/09 | Experimento mínimo de viabilidade; esquema do banco e importador | Descrever dados, preparação, arquitetura e critérios de teste |
| 10/09 | Indicadores, filtros e primeira interface conectada | Registrar implementação efetiva; desenvolver fundamentação |
| 11/09 | Lista de oportunidades; integrar pontuação somente se defensável | Documentar experimento, resultados medidos e limitações |
| 12/09 | Testes ponta a ponta; corrigir erros; preparar execução reproduzível | Revisar referências, coerência e capturas da aplicação real |
| 13/09 | Congelar versão, executar roteiro de demonstração e empacotar | Revisar e entregar versão parcial; explicitar trabalho restante |

## Critérios de aceite

- Um CSV válido é importado e uma reimportação não duplica os registros silenciosamente.
- Um CSV inválido produz erros claros com linha e campo.
- Totais e filtros do dashboard conferem com cálculos de referência.
- A lista distingue oportunidades abertas, ganhas e perdidas quando a fonte permitir.
- Regras não são apresentadas como machine learning; pontuações experimentais não são apresentadas como probabilidades validadas.
- O experimento, se viável, mantém avaliação separada do treinamento e impede uso de informações posteriores à decisão.
- A demonstração tem instruções de execução e dados identificados como reais ou fictícios.
- O texto distingue proposta, implementação e evidência; não contém resultados inventados.

## Corte de escopo se necessário

Preservar importação, banco, indicadores corretos, demonstração reproduzível e metodologia honesta. Adiar chat com LLM, Excel, integrações externas, automações de contato e acabamento visual avançado. Deploy público é desejável, mas uma execução local reproduzível serve à entrega parcial se a instituição não exigir publicação. Não publicar dados de clientes nem expor uma aplicação multiempresa sem verificar isolamento e acesso.

## Decisão sobre a base

Maven CRM Sales Opportunities foi selecionada para a demonstração técnica B2B. A fonte declara dados fictícios e seu download oficial exige login. A cópia pública utilizada tem proveniência, revisão e hashes documentados, mas não foi comparada byte a byte com o pacote oficial autenticado. Ela é adequada para testar importação, indicadores e arquitetura; não permite alegar validade ou impacto comercial em empresas reais.

Fonte consultada: https://mavenanalytics.io/data-playground/crm-sales-opportunities

## Participação do autor

Fornecer modelo/regras de formatação da instituição e observações do orientador quando disponíveis. Revisar e compreender as decisões e o código para a defesa. Se possível, conversar com um gestor ou vendedor sobre como escolhe oportunidades e quais informações faltam; entrevista exploratória não equivale a comprovação de mercado.

## Progresso registrado em 08/09/2026

- Concluído: obtenção com revisão e hashes, auditoria dos quatro arquivos de dados e decisão de uso com limitações.
- Concluído: esquema SQLite multiempresa e importador idempotente com validação de linha/campo.
- Concluído: experimento inicial com divisão temporal, baseline, regressão logística e árvore de decisão.
- Concluído antecipadamente da etapa de 10/09: consultas de indicadores, API local e dashboard responsivo conectado ao banco.
- Concluído: fila de oportunidades abertas com filtros, paginação e regras transparentes de revisão.
- Concluído: tela local para envio controlado dos quatro CSVs, com limite de tamanho, diretório temporário e importação somente após validação integral.
- Concluído: vinte e dois testes automatizados e verificação visual da interface e da nova tela de autenticação em larguras de celular e desktop.
- Concluído além do escopo da entrega parcial: projeto Supabase vigente criado em São Paulo; seis migrations aplicadas e verificadas no PostgreSQL 17 com modelo multiempresa, índices, privilégios, RLS, provisionamento seguro e RPCs analíticas e de importação.
- Concluído além do escopo da entrega parcial: autenticação integrada ao FastAPI e à interface com cookies HttpOnly; rotas analíticas exigem sessão e importações exigem papel `owner` ou `admin`.
- Concluído além do escopo da entrega parcial: adaptador Supabase para indicadores, filtros, fila e importação atômica; a organização é sempre derivada da sessão, não do parâmetro enviado pelo cliente.
- Concluído em rascunho separado: fundamentação sobre gestão do pipeline, lead scoring, avaliação preditiva, explicabilidade e assistente com consultas controladas, apoiada por seis referências acadêmicas verificadas.
- Concluído: introdução revisada, problema, justificativa, objetivos e delimitação alinhados ao novo recorte B2B.
- Concluído: rascunho acadêmico consolidado em Word com 20 páginas, resumo, abstract, sumário automático, diagrama de arquitetura e captura da aplicação real.
- Concluído: conferência visual integral das 20 páginas, com paginação, figuras e tabela do experimento preservadas.
- Em desenvolvimento: adequação fina ao manual institucional, ampliação da metodologia e revisão com o orientador.
- Em desenvolvimento: ativação ponta a ponta do modo Supabase; código, migrations e testes transacionais estão prontos, mas a primeira conta real e a carga permanente dos dados ainda estão pendentes.
- Não iniciado: assistente com LLM, avaliação com usuários e deploy.

## Situação em relação ao cronograma

| Etapa | Situação em 08/09/2026 |
| --- | --- |
| 07–08/09 | Concluída |
| 09/09 | Concluída antecipadamente |
| 10/09 | Concluída antecipadamente |
| 11/09 | Núcleo concluído antecipadamente; ML corretamente mantido fora da interface por falta de evidência |
| 12/09 | Parcialmente concluída: testes, coerência básica e capturas prontas; revisão bibliográfica fina pendente |
| 13/09 | Pendente: congelar versão, executar roteiro de demonstração e empacotar a entrega |

Estimativa de avanço para a entrega de domingo: software demonstrável em aproximadamente 98%; texto parcial em aproximadamente 78% do conteúdo planejado e 68% de prontidão formal. Em relação ao produto final, o software está próximo de 72%, pois ativação com contas reais, assistente, validação com usuários e deploy ainda são partes relevantes. Percentuais são estimativas de escopo, não métricas objetivas de qualidade.
