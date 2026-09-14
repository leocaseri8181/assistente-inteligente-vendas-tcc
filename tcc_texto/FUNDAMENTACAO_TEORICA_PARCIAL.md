# Fundamentação teórica

> Texto de trabalho para integração ao documento institucional. A numeração final das seções e a formatação das referências devem seguir o manual da instituição. As fontes abaixo foram verificadas em seus registros acadêmicos; exemplos de outras empresas são tratados como evidência contextual, não como comprovação do protótipo desenvolvido neste trabalho.

## Sistemas de informação aplicados à gestão comercial

A gestão de vendas depende de informações distribuídas entre cadastros de clientes, produtos, vendedores, atividades e oportunidades. Um sistema de CRM organiza parte desses registros, mas o armazenamento isolado não produz, por si só, uma decisão comercial. Para apoiar o gestor, os dados precisam ser submetidos a regras de qualidade, agregados em indicadores com definições explícitas e apresentados no contexto em que uma ação será tomada.

Nesse cenário, a análise do funil comercial pode ser entendida como um problema de apoio à decisão. Indicadores descritivos respondem a perguntas sobre o que foi registrado, como quantidade de negócios por estágio, valor de fechamentos e taxa observada de ganho. Modelos preditivos procuram responder a outra pergunta: qual desfecho é mais provável para uma oportunidade ainda não encerrada? A separação é importante porque um total histórico é diretamente calculável, enquanto uma estimativa sobre o futuro depende da população estudada, do instante de previsão, das variáveis disponíveis e da validação fora dos dados usados no treinamento.

Yan et al. (2015, p. 1, tradução nossa) definem a previsão de propensão de ganho como “a estimativa quantitativa da probabilidade de que oportunidades de vendas em andamento sejam ganhas dentro de uma janela de tempo especificada”. Os autores relacionam essa estimativa à gestão proativa do pipeline e à alocação de recursos, mas também destacam dificuldades próprias do contexto B2B: quantidade de transações menor do que em mercados B2C, dados ruidosos e mudanças rápidas no ambiente comercial. Esses fatores ajudam a explicar por que não se deve supor que qualquer histórico de CRM seja suficiente para produzir previsões confiáveis.

## Lead scoring e priorização de oportunidades

Lead scoring é o processo de atribuir uma medida de qualidade ou prioridade a contatos e oportunidades comerciais. Essa medida pode ser construída por pontos definidos por especialistas, por métodos estatísticos ou por algoritmos de aprendizado de máquina. O resultado costuma apoiar a ordenação do trabalho: em vez de analisar todos os registros com a mesma urgência, a equipe concentra atenção nos casos considerados mais relevantes.

A revisão sistemática de Wu, Andreev e Benyoucef (2024) identifica abordagens tradicionais baseadas em regras e abordagens preditivas baseadas em dados. O levantamento também mostra que os estudos avaliam os modelos por medidas técnicas — como precisão, revocação, AUC e lift — e por resultados comerciais — como conversão, redução de custos e receita. Essa distinção é essencial: um classificador pode apresentar uma métrica estatística favorável sem que tenha sido demonstrado impacto econômico no processo em que será utilizado.

O trabalho de González-Flores, Rubiano-Moreno e Sosa-Gómez (2025) apresenta um estudo de caso de priorização B2B apoiada por análise de dados e aprendizado de máquina. Sua relevância para esta pesquisa está menos em sugerir um algoritmo universal e mais em mostrar que o modelo precisa ser desenvolvido de acordo com os dados, o processo de qualificação e o objetivo comercial de uma organização. Portanto, o protótipo deste TCC distingue dois níveis de priorização. O primeiro usa regras operacionais explícitas, adequadas para a demonstração mesmo quando não há evidência preditiva suficiente. O segundo é um experimento supervisionado, cuja adoção depende de desempenho medido e de dados representativos.

Uma regra explícita não é automaticamente correta ou neutra. O limite de dias que caracteriza uma oportunidade antiga, por exemplo, precisa ser revisado com usuários do domínio e pode variar entre empresas, produtos e ciclos de venda. Sua vantagem inicial é ser auditável: o vendedor consegue saber qual condição foi aplicada e contestá-la. No protótipo, falta de conta e idade desde o engajamento funcionam como sinais de revisão, não como probabilidade de fechamento e não como afirmação de que um novo contato causará a venda.

## Aprendizado de máquina no pipeline de vendas

Em um problema supervisionado de classificação, o modelo aprende relações entre variáveis disponíveis e rótulos históricos. No caso estudado, os rótulos são os estados `Won` e `Lost`. A definição do instante de previsão antecede a escolha do algoritmo. Se a aplicação pretende apoiar a decisão no início do estágio de engajamento, ela não pode usar data de fechamento, valor final ou qualquer outro campo produzido depois desse instante. O uso dessas variáveis criaria vazamento de informação e uma avaliação artificialmente otimista.

Rezazadeh (2020) propõe um fluxo de modelagem preditiva para vendas B2B que separa treinamento e inferência e inclui enriquecimento de atributos, modelos probabilísticos e fronteiras de decisão. O estudo foi avaliado em dados reais de uma empresa de consultoria. Já Yan et al. (2015) apresentam uma estrutura para estimar propensão de ganho em oportunidades ao longo do pipeline. Em conjunto, os trabalhos mostram a viabilidade da modelagem, mas não eliminam a necessidade de reavaliar cada implementação em sua própria população.

A comparação precisa incluir procedimentos simples de referência. Uma prevalência constante mostra o resultado esperado sem capacidade de ordenar oportunidades; uma taxa histórica por produto verifica se uma segmentação básica já explica parte do resultado. Comparar somente algoritmos mais complexos pode esconder que nenhum deles oferece ganho útil em relação a um *baseline* simples.

A avaliação temporal também é coerente com o uso pretendido. Treinar em registros posteriores e testar em registros anteriores permite que padrões futuros influenciem a construção do modelo, situação incompatível com a implantação. Por isso, o experimento deste trabalho ordenou oportunidades pela data de engajamento e reservou o período mais recente para teste. O desempenho foi medido por Average Precision, ROC AUC, Brier score e precisão e lift no grupo superior do ranking. As métricas têm papéis diferentes: discriminação, qualidade das probabilidades e utilidade da ordenação não devem ser confundidas.

No experimento preliminar deste TCC, a regressão logística e a árvore de decisão não apresentaram melhora conclusiva em relação à prevalência no teste temporal. Por isso, a aplicação não expõe as saídas desses modelos como probabilidades confiáveis. O resultado limita a conclusão desta etapa e aponta a necessidade de coletar histórico de atividades, motivos de perda e informações comerciais autorizadas.

## Explicabilidade e participação humana

Uma pontuação comercial interfere na distribuição de tempo da equipe. Mesmo que o sistema não execute uma decisão automaticamente, uma lista ordenada pode induzir vendedores a ignorar oportunidades colocadas no fim do ranking. Por isso, a interface precisa apresentar o significado da medida, os dados utilizados e os limites conhecidos.

No contexto de decisões de alto impacto, Rudin (2019, p. 206, tradução nossa) afirma que “o caminho é projetar modelos inerentemente interpretáveis”. Vendas não é equiparada, neste trabalho, aos domínios de alto risco analisados pela autora. O ponto é usado como princípio de projeto: quando não há benefício preditivo demonstrado, não há motivo para trocar regras legíveis por um modelo opaco.

Jena, Yang e Tan (2023) descrevem um sistema de priorização de contas integrado ao CRM do LinkedIn. Além de modelos de recomendação, a solução produz explicações no nível da conta. Os autores relatam que vendedores queriam conhecer as razões das pontuações e compará-las com seu conhecimento do domínio. O estudo utilizou teste A/B estratificado, com aproximadamente 4,5 mil contas em cada condição durante seis meses, e relatou aumento de 8,08% na métrica de crescimento incremental de renovações entre as contas tratadas. O próprio artigo delimita desafios como amostra de vendedores, efeitos defasados pelo ciclo comercial, equidade da randomização e adoção da ferramenta.

Esse caso demonstra que desempenho offline e efeito no processo são evidências diferentes. O experimento retrospectivo do presente TCC avalia previsão; ele não mede se apresentar uma fila altera comportamento, conversão ou receita. Uma etapa futura deverá observar usuários em tarefas definidas e, caso exista implantação real, formular uma comparação que preserve grupo de referência, duração compatível com o ciclo de vendas e métricas previamente escolhidas.

## Assistente em linguagem natural com consultas controladas

Uma interface em linguagem natural pode reduzir a distância entre perguntas de negócio e filtros técnicos. Contudo, o modelo de linguagem não deve se tornar a fonte dos números. A arquitetura proposta atribui ao backend a execução de funções determinísticas, como calcular a taxa de ganho para um período ou listar oportunidades segundo critérios autorizados. O assistente recebe o resultado estruturado e atua na interpretação e na apresentação da resposta.

Com essa divisão, período, filtros, denominador e consulta podem ser registrados sem depender do texto gerado. Ela também reduz o risco de o assistente interpretar conteúdo de um CSV como instrução ou calcular totais por aproximação linguística. A API e as consultas controladas constituem a base dessa arquitetura. A camada de linguagem natural integra o escopo final do protótipo, porém seus resultados somente serão incorporados à avaliação após a implementação e os testes correspondentes.

O assistente também deverá reconhecer perguntas que os dados não respondem. A base atual não contém registro de contatos, e-mails, telefonemas nem intervenções. Consequentemente, o sistema pode calcular dias desde o engajamento, mas não pode informar dias desde o último contato. Da mesma forma, uma associação entre atributo e vitória não demonstra que uma ação sobre esse atributo aumentará a conversão.

## Síntese e relação com a solução proposta

A literatura sustenta que priorização e previsão são problemas relevantes na gestão do pipeline B2B e que modelos podem apoiar a alocação de recursos. Também evidencia que o valor de uma solução depende de integração ao processo, explicações compreensíveis e avaliação que ultrapasse uma única métrica técnica. As condições encontradas neste projeto — dados fictícios, ausência de atividades e mudança temporal — exigem uma implementação mais restrita do que alguns casos industriais.

O projeto segue uma sequência definida: os arquivos são validados e armazenados; em seguida, o sistema apresenta indicadores e uma fila auditável; os modelos são comparados com *baselines* em um teste temporal; por fim, o assistente deverá formular respostas a partir das funções analíticas verificadas. Somente componentes com evidência suficiente poderão ser usados na priorização. Dessa forma, o trabalho relaciona engenharia de software, análise de dados e avaliação acadêmica sem assumir que a inteligência artificial produzirá benefício por si só.

## Referências

GONZÁLEZ-FLORES, Laura; RUBIANO-MORENO, Jessica; SOSA-GÓMEZ, Guillermo. The relevance of lead prioritization: a B2B lead scoring model based on machine learning. *Frontiers in Artificial Intelligence*, v. 8, 2025. DOI: https://doi.org/10.3389/frai.2025.1554325. Disponível em: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1554325/full. Acesso em: 14 set. 2026.

JENA, Suvendu; YANG, Jilei; TAN, Fangfang. Unlocking sales growth: account prioritization engine with explainable AI. arXiv:2306.07464, 2023. Disponível em: https://arxiv.org/abs/2306.07464. Acesso em: 14 set. 2026.

REZAZADEH, Alireza. A generalized flow for B2B sales predictive modeling: an Azure Machine-Learning approach. *Forecasting*, v. 2, n. 3, p. 267-283, 2020. DOI: https://doi.org/10.3390/forecast2030015. Disponível em: https://www.mdpi.com/2571-9394/2/3/15. Acesso em: 14 set. 2026.

RUDIN, Cynthia. Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. *Nature Machine Intelligence*, v. 1, p. 206-215, 2019. DOI: https://doi.org/10.1038/s42256-019-0048-x. Disponível em: https://www.nature.com/articles/s42256-019-0048-x. Acesso em: 14 set. 2026.

WU, Migao; ANDREEV, Pavel; BENYOUCEF, Morad. The state of lead scoring models and their impact on sales performance. *Information Technology and Management*, v. 25, p. 69-98, 2024. DOI: https://doi.org/10.1007/s10799-023-00388-w. Disponível em: https://link.springer.com/article/10.1007/s10799-023-00388-w. Acesso em: 14 set. 2026.

YAN, Junchi et al. Sales pipeline win propensity prediction: a regression approach. arXiv:1502.06229, 2015. Disponível em: https://arxiv.org/abs/1502.06229. Acesso em: 14 set. 2026.
