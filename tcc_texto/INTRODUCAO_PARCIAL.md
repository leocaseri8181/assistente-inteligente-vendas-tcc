# Introdução

## Contextualização e justificativa

Equipes comerciais registram clientes, produtos, vendedores e oportunidades em planilhas ou sistemas de relacionamento com clientes. Esses registros permitem acompanhar o funil de vendas, mas seu volume e sua fragmentação podem dificultar a comparação entre períodos, a identificação de problemas de qualidade e a escolha dos casos que exigem atenção. A necessidade prática não é apenas armazenar dados, mas transformá-los em informação verificável para apoiar a rotina do gestor e do vendedor.

No contexto business-to-business (B2B), a priorização é particularmente relevante porque os ciclos de venda podem ser longos e cada profissional administra um número limitado de contas e oportunidades. Yan et al. (2015) relacionam a previsão de propensão de ganho à gestão proativa do pipeline e à alocação de recursos. Os autores também apontam dificuldades do contexto B2B, como menor número de transações, ruído nos dados e mudanças no ambiente comercial. Portanto, o uso de aprendizado de máquina depende da qualidade dos registros, do instante em que a previsão é realizada e da validação em dados que não participaram do treinamento.

A revisão sistemática de Wu, Andreev e Benyoucef (2024) identifica modelos tradicionais de *lead scoring* baseados em regras e modelos preditivos baseados em dados. Os estudos revisados usam tanto métricas técnicas quanto medidas de desempenho comercial. Essa diferença importa neste trabalho: classificar registros históricos não prova, por si só, aumento de conversão, redução de custos ou crescimento de receita em uma empresa real.

Com base nesse problema, este trabalho propõe um protótipo de análise de vendas voltado inicialmente a pequenas e médias empresas B2B. O escopo funcional estabelecido para o produto inclui importação de dados comerciais estruturados, validação de inconsistências, cálculo de indicadores, fila de oportunidades com critérios visíveis e um assistente em linguagem natural ligado a consultas controladas do backend. Um experimento de aprendizado de máquina compara modelos com procedimentos simples de referência. A camada de linguagem natural deverá apresentar resultados calculados pelo sistema, preservando filtros, períodos, denominadores e limitações dos dados.

A contribuição acadêmica combina o desenvolvimento de software com uma avaliação empírica inicial. A aplicação é executável e testável, e o experimento verifica se os campos disponíveis sustentam uma priorização preditiva. A documentação também registra os limites encontrados durante a implementação. No uso comercial, o recorte busca reduzir o tempo gasto para conferir planilhas e decidir onde concentrar a análise. A versão inicial não substitui o julgamento do profissional nem automatiza contatos com clientes.

## Problema de pesquisa

Em que medida um protótipo que combina indicadores comerciais, regras auditáveis, aprendizado de máquina e uma interface em linguagem natural pode apoiar a análise e a priorização de oportunidades de vendas B2B quando comparado a procedimentos simples de referência?

## Objetivo geral

Desenvolver e avaliar um protótipo de aplicação para importar dados comerciais, apresentar indicadores e apoiar a análise e a priorização de oportunidades B2B por critérios verificáveis e consultas em linguagem natural.

## Objetivos específicos

- Selecionar uma base de demonstração compatível com o problema e documentar sua origem, licença e limitações.
- Implementar um processo reproduzível de importação, validação e armazenamento dos dados.
- Definir indicadores comerciais com períodos, filtros e denominadores explícitos.
- Construir uma interface que permita acompanhar o funil e revisar oportunidades abertas.
- Comparar modelos de classificação com baselines por meio de uma separação temporal entre treino e teste.
- Evitar o uso de informações posteriores ao instante de decisão no treinamento e na avaliação.
- Integrar uma interface em linguagem natural baseada em funções analíticas controladas pelo backend.
- Avaliar a correção funcional do software, a qualidade das respostas analíticas, as limitações dos dados e as condições necessárias para validação com usuários reais.

## Delimitação

O público-alvo inicial é formado por gestores e profissionais de vendas de pequenas e médias empresas B2B que possuam histórico comercial exportável em formato tabular. A demonstração utiliza dados fictícios e públicos, adequados para verificar a execução técnica, mas insuficientes para demonstrar impacto em organizações reais.

O escopo funcional do protótipo inclui ingestão de arquivos CSV com estrutura conhecida, persistência relacional, indicadores descritivos, filtros, fila de revisão, experimento preditivo retrospectivo e um assistente que utiliza funções analíticas autorizadas. O assistente não executará consultas arbitrárias nem tomará decisões em nome do usuário. Integrações diretas com CRMs, WhatsApp, envio automático de mensagens, cobrança, análise genérica de PDF ou Word, previsão de valor vitalício e decisões comerciais autônomas ficam fora do trabalho.

Também se distingue previsão de causalidade. Estimar associação entre atributos e o desfecho de uma oportunidade não demonstra que realizar um contato ou alterar uma condição produzirá uma venda. Qualquer avaliação de impacto exigirá desenho específico, duração compatível com o ciclo comercial e participação de uma organização autorizada.
