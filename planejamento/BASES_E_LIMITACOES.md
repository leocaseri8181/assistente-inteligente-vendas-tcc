# Seleção de bases e limitações

Este documento começou como revisão documental das candidatas. Em 08/09/2026, os arquivos Maven foram obtidos de um espelho público com revisão fixada e auditados localmente. Os resultados próprios estão em `AUDITORIA_DADOS.md` e `artifacts/audit.json`. Olist e UCI permanecem apenas na revisão documental.

## Olist Marketing Funnel

Fonte: https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist

A descrição publicada informa 8 mil leads qualificados, amostrados entre junho de 2017 e junho de 2018, com dados anonimizados. As tabelas são de leads e negócios fechados. A contagem de 842 fechamentos citada na conversa veio de material secundário e precisa de confirmação nos arquivos.

Licença indicada pelo catálogo: CC BY-NC-SA 4.0. Referência: https://creativecommons.org/licenses/by-nc-sa/4.0/

A licença inclui atribuição, uso não comercial e compartilhamento de adaptações sob as condições especificadas. A recomendação anterior omitiu essa restrição relevante para a intenção de vender o produto. Manter a avaliação acadêmica separada de qualquer uso comercial dessa base e de seus derivados até verificar as condições aplicáveis.

Questões para auditoria:

- Quais campos existem para todos os leads e quais somente para os convertidos?
- Ausência em negócios fechados significa apenas fechamento não observado? Não rotular automaticamente como perda definitiva.
- Há data de encerramento da observação? A última data encontrada não prova acompanhamento completo de todos os leads.
- É possível definir conversão observada em uma janela fixa, com acompanhamento suficiente para cada exemplo?
- Origem e página de entrada contêm sinal preditivo fora do período de treinamento?
- A junção com e-commerce é parcial? O identificador de vendedor corresponde à empresa captada, não ao consumidor final que faz um pedido.

Campos presentes apenas nos convertidos, datas e valores de fechamento não devem alimentar uma previsão na entrada do lead. Não prometer análise de margem, gastos de marketing, contatos ou motivos de perda sem esses dados.

Decisão: candidata acadêmica; inadequado declarar antecipadamente que é a melhor base de ML ou que o modelo poderá ser vendido.

## Maven CRM Sales Opportunities

Fontes primárias:

- https://mavenanalytics.io/guided-projects/sales-pipeline-analysis
- https://mavenanalytics.io/data-playground/crm-sales-opportunities

O fornecedor descreve empresa fictícia B2B de hardware, com contas, produtos, equipes e oportunidades. A página do projeto guiado anuncia 8.800 registros e 18 campos; a página de download apresentou metadados discrepantes (499 registros, 25 campos e categorias de viagem/clima), apesar de manter a descrição de CRM. Usar arquivos para resolver a divergência.

A página de download indica Public Domain e origem data.world. Registrar licença e proveniência do pacote efetivamente obtido. O download mostrado solicita login. Não tratar uma cópia de terceiros como fonte original sem documentá-la.

Auditoria concluída: 8.800 oportunidades, 85 contas, 7 produtos e 35 registros de vendedores. Foram encontrados 4.238 negócios ganhos, 2.473 perdidos, 1.589 em engajamento e 500 em prospecção. Há 1.480 ocorrências de `GTXPro` no pipeline enquanto o cadastro usa `GTX Pro`; a transformação é explícita e o valor original é preservado.

Decisão: aprovada para o protótipo B2B e para um experimento retrospectivo com ressalvas. O caráter fictício aparece na metodologia e na demonstração. A cópia pública foi fixada por revisão e hashes, mas não foi comparada byte a byte com o download oficial autenticado.

## UCI Bank Marketing

Fonte: https://archive.ics.uci.edu/dataset/222/bank+marketing

DOI: https://doi.org/10.24432/C5K306

Licença informada pela UCI: CC BY 4.0. Campanhas bancárias portuguesas com resposta à contratação de depósito. Existem variantes com 45.211 e 41.188 registros; escolher e documentar uma única variante antes de reportar resultados.

Duração da chamada não está disponível antes da chamada. Evitar usá-la para priorizar contatos futuros. Variáveis de campanha também exigem interpretação do instante da decisão.

Decisão: alternativa para estudo de propensão de resposta em campanhas, com mudança explícita de domínio. Não misturar registros com Olist ou Maven, nem transferir diretamente o modelo para B2B.

## Condição para aprovação da base

A escolha final exige arquivos acessíveis, licença identificada, alvo defensável e variáveis anteriores à decisão. O teste inicial deve medir se há sinal além de uma regra simples. Dados fictícios podem testar software; evidência de utilidade comercial exige validação com usuários e, posteriormente, dados de clientes autorizados.
