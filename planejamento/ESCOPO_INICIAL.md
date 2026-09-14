# Sistema inteligente de análise de vendas e priorização de oportunidades

Status: proposta de trabalho v0.1, sujeita à auditoria da base e ao alinhamento com o orientador.

## Produto e público

Aplicação web para gestores comerciais de pequenas e médias empresas B2B que utilizam planilhas ou exportações de CRM. A proposta é transformar o histórico comercial em indicadores verificáveis, uma lista de oportunidades para revisão e respostas em linguagem natural.

A hipótese de dor é a dificuldade de consolidar informações e escolher quais oportunidades revisar. Ainda não houve entrevista com clientes; disposição a pagar e impacto comercial permanecem hipóteses.

## Fluxo principal

1. Gestor importa dados e confirma o significado das colunas.
2. Sistema mostra erros, duplicidades e campos ausentes antes de confirmar a importação.
3. Dashboard apresenta resultados por período e dimensões disponíveis.
4. Gestor consulta oportunidades e os critérios de ordenação.
5. Assistente responde perguntas utilizando resultados calculados pelo sistema.
6. Gestor registra a ação escolhida e acompanha o resultado.

Exemplo de tarefa: identificar a evolução das vendas do período, selecionar oportunidades para revisão e entender os dados que sustentam a seleção.

## MVP

| Entrega | Critério de aceitação |
| --- | --- |
| Importação CSV com modelo documentado | Arquivos válidos são carregados; erros apontam linha e campo; reimportação não duplica registros silenciosamente |
| Dashboard comercial | Totais e filtros conferem com consultas de referência; período e definição de cada indicador ficam explícitos |
| Lista de oportunidades | Exibe status, responsável e critérios de prioridade disponíveis, incluindo ausência de informação |
| Experimento de ML | Compara baseline e modelos com avaliação separada do treinamento e campos disponíveis no momento da previsão |
| Assistente analítico | Respostas numéricas usam funções de consulta controladas, indicam período e não inventam campos ausentes |
| Registro de ações | Usuário confirma e registra ações; sugestões não são enviadas automaticamente a clientes |
| Acesso e isolamento | Dados de uma empresa não ficam acessíveis a usuários de outra; verificar com teste negativo |
| Demonstração reproduzível | Procedimento documentado permite executar o sistema, importar amostra e reproduzir o experimento |

Excel poderá ser incluído após o importador CSV. WhatsApp, extração de PDF/Word, integrações diretas com CRMs, cobrança e previsão de valor do cliente ficam para fases posteriores.

## Indicadores e limites

- Valor de negócios ganhos: soma dos valores dos negócios marcados como ganhos. Não chamar de receita contábil sem dados que comprovem esse significado.
- Taxa de ganho: ganhos / (ganhos + perdidos), quando a base distinguir ambos. Oportunidades abertas não entram nesse denominador.
- Valor médio dos negócios ganhos: valor total ganho / número de negócios ganhos.
- Duração do ciclo: diferença entre datas documentadas de início e fechamento; explicitar a população usada.
- Volume de oportunidades por status, responsável, produto e período, somente quando esses campos existirem.
- Tempo sem contato exige histórico de contatos. Tempo desde entrada no funil não é equivalente a tempo sem contato.
- Margem exige custos; alcance de metas exige metas; retorno de marketing exige gastos. Não fabricar esses indicadores.

## Núcleo acadêmico

Título provisório: Desenvolvimento e avaliação de um assistente inteligente para análise de vendas e priorização de oportunidades comerciais.

Pergunta: em que medida um sistema que combina indicadores comerciais, aprendizado de máquina e uma interface em linguagem natural apoia a análise e a priorização de oportunidades, em comparação com procedimentos de referência?

Objetivo geral: desenvolver e avaliar uma aplicação que permita consultar indicadores comerciais e priorizar oportunidades com critérios verificáveis.

Objetivos específicos:

1. Selecionar e documentar uma base compatível com a pergunta de pesquisa.
2. Implementar importação, validação e consultas analíticas reproduzíveis.
3. Comparar uma regra de referência com modelos de classificação ou ordenação, conforme o alvo viável.
4. Integrar respostas em linguagem natural fundamentadas em consultas controladas.
5. Avaliar qualidade preditiva, correção das respostas e execução de tarefas pelos usuários.

Método proposto: pesquisa aplicada, desenvolvimento de software e avaliação experimental retrospectiva. A avaliação com usuários depende de participantes, prazo e requisitos da instituição. Resultados de bases públicas ou simuladas não comprovam aumento de vendas em clientes reais.

## Desenho do experimento

Definir antes do treinamento a unidade de análise, instante da previsão, horizonte do resultado e quais informações seriam conhecidas naquele instante.

Comparar baseline simples, regressão logística e um modelo de árvores. Selecionar hiperparâmetros e calibrar probabilidades usando apenas treinamento/validação. Reservar teste final. Separar temporalmente quando datas e acompanhamento permitirem; documentar outra estratégia se não permitirem. Agregações históricas devem usar somente dados anteriores à previsão, inclusive desfechos já conhecidos naquele instante.

Avaliar PR-AUC, precisão e recuperação no topo da lista, lift em relação ao baseline e calibração quando houver probabilidades. Registrar proporção de positivos, tamanho do conjunto de teste, incerteza e sensibilidade ao corte da lista. Um bom resultado não é garantido: ausência de ganho é um resultado científico válido.

Não confundir maior probabilidade de compra com maior benefício causado pelo contato do vendedor. O ranking de propensão é apoio à revisão; demonstrar o efeito de uma ação requer outro desenho experimental.

Para o assistente, preparar perguntas com respostas calculadas por consultas de referência. Incluir filtros, períodos sem registros, perguntas ambíguas e dados ausentes. Medir correção numérica, fundamentação, resposta adequada à ausência de dados, latência e custo por tarefa quando houver integração.

## Arquitetura conceitual

Interface web → backend com autenticação e regras de negócio → banco relacional e arquivos importados.

O backend mantém módulos de importação, métricas, pontuação e histórico de ações. O assistente consulta funções autorizadas desses módulos. Dados importados e textos recuperados são conteúdo, não instruções para executar comandos.

Tecnologias específicas e hospedagem serão registradas em decisão posterior, após conferir ambiente e documentação. Os plugins de desenvolvimento não serão requisitos para o cliente usar o produto.

## Dados e viabilidade comercial

Olist Marketing Funnel segue como candidata acadêmica, sem decisão final. Possui restrição não comercial e exige verificação do alvo e do período observado. Não embutir a base nem um modelo derivado dela na versão comercial sem resolver as condições aplicáveis.

Maven CRM Sales Opportunities é candidata para protótipo B2B, explicitamente fictícia. Resultados nela não demonstram generalização a empresas reais. Bank Marketing representa outro setor e não deve ser usado para alegar validação do modelo B2B.

A versão comercial deverá receber dados autorizados de cada cliente e avaliar se existe histórico suficiente. Na ausência de histórico adequado, pode oferecer indicadores e regras transparentes sem exibir uma probabilidade de conversão sem suporte.

## Próximas entregas

1. Obter arquivos da base e registrar origem, versão, licença e hash.
2. Auditar colunas, junções, valores ausentes, datas, disponibilidade temporal das variáveis e construção do alvo.
3. Decidir a base e limitar o experimento ao que os dados sustentam.
4. Implementar uma pequena comparação de baseline/modelos para testar viabilidade antes da interface completa.
5. Implementar importação e indicadores; depois integrar pontuação e assistente.

## Informações ainda necessárias

Entrega parcial acordada: domingo, 13/09/2026. Meta do usuário: aproximadamente 50–60% do software e 70% do texto, incluindo desenvolvimento parcial. Esses percentuais são metas de escopo, não uma medição de progresso já alcançado. A data final ainda não foi definida. O autor informou disponibilidade flexível, sem um limite de horas especificado.

Ainda necessários: formato exigido pela UNIARA; orientações recebidas do professor; orçamento de hospedagem/API; possibilidade de entrevistar gestores ou vendedores. Essas informações ajustam a avaliação, sem impedir a auditoria inicial. O plano da entrega parcial está em CRONOGRAMA_PARCIAL.md.
