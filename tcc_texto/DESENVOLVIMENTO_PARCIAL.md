# Desenvolvimento e avaliação do sistema

## Delimitação do problema

Equipes comerciais acumulam dados de oportunidades em planilhas e sistemas de relacionamento com clientes, mas a existência dos registros não garante que gestores consigam interpretá-los ou decidir quais casos devem ser revisados primeiro. O projeto delimita esse problema ao contexto de pequenas e médias empresas B2B que possuem histórico comercial exportável em formato tabular. O protótipo final deverá importar esses dados, verificar sua qualidade, produzir indicadores com definições explícitas, apresentar uma lista de oportunidades acompanhada dos critérios de ordenação e permitir consultas em linguagem natural por meio de funções analíticas controladas.

O projeto não pretende substituir a decisão do vendedor nem afirmar que um contato causará uma venda. A probabilidade de um desfecho e o efeito causado por uma ação comercial são questões distintas. Também ficam fora do escopo inicial integrações diretas com CRMs, envio automático de mensagens, leitura genérica de documentos, cobrança e previsão de valor vitalício do cliente.

## Problema de pesquisa e objetivos

A pergunta de pesquisa é: em que medida um protótipo que combina indicadores comerciais, regras auditáveis, aprendizado de máquina e uma interface em linguagem natural apoia a análise e a priorização de oportunidades em comparação com procedimentos de referência?

O objetivo geral é desenvolver e avaliar um protótipo para consulta de indicadores comerciais e priorização de oportunidades com critérios verificáveis. Os objetivos específicos são selecionar e documentar uma base compatível, implementar importação e validação reproduzíveis, comparar modelos com baselines, integrar respostas em linguagem natural fundamentadas em consultas controladas e avaliar a correção das funções desenvolvidas.

## Método

O trabalho é uma pesquisa aplicada que combina desenvolvimento de software e avaliação experimental retrospectiva. A primeira avaliação utiliza dados públicos fictícios para testar a viabilidade técnica. Essa escolha permite reproduzir a importação e o experimento, mas não comprova impacto em empresas reais. A validação comercial exigirá entrevistas e, posteriormente, dados autorizados de organizações que representem o público-alvo.

O desenvolvimento segue entregas incrementais. Cada funcionalidade recebe um critério verificável: a importação deve informar linha e campo em dados inválidos; a reimportação não pode duplicar registros silenciosamente; indicadores devem conferir com consultas de referência; e o experimento preditivo deve separar treino e teste antes de aprender transformações. Resultados só são incorporados ao texto depois de executados.

## Caracterização da pesquisa

O estudo possui natureza aplicada, pois produz e examina um artefato de software destinado a apoiar a análise de oportunidades comerciais. A investigação combina revisão bibliográfica, construção incremental do protótipo, auditoria de dados, testes funcionais e um experimento quantitativo retrospectivo. A revisão fundamenta as decisões relacionadas a lead scoring, avaliação preditiva, explicabilidade e participação humana. A parte experimental verifica o comportamento do sistema e mede o desempenho dos modelos na base selecionada.

O objeto da pesquisa é o protótipo definido por seu escopo final, que inclui importação, indicadores, priorização e consultas em linguagem natural. A avaliação apresentada no texto considera somente os componentes para os quais já existem execução e evidência registradas. Foram adotadas três formas de evidência: correção funcional, desempenho preditivo retrospectivo e utilidade no processo comercial. Os testes automatizados tratam da correção funcional, enquanto a separação temporal entre treino e teste permite examinar o desempenho preditivo. A utilidade comercial dependerá da observação de usuários e de dados de organizações reais.

## Coleta e preparação dos dados

A demonstração utiliza o conjunto CRM Sales Opportunities, descrito pela Maven Analytics como uma base fictícia de vendas B2B (MAVEN ANALYTICS, 2026). Foram obtidos quatro arquivos de dados e um dicionário de campos de um espelho público fixado por revisão. Para permitir reprodução, registraram-se a origem, a data de obtenção, o tamanho e o resumo criptográfico SHA-256 de cada arquivo. Os arquivos brutos foram preservados sem alteração.

A preparação começou por uma auditoria de cabeçalhos, tipos, chaves, referências, valores ausentes e coerência temporal. Contas, produtos e vendedores foram confrontados com as oportunidades. A divergência entre `GTXPro` e `GTX Pro` foi tratada por um alias explícito, mantendo-se também o valor original. Ausências compatíveis com o estágio do funil não foram preenchidas artificialmente. Após a validação integral do lote, os registros foram inseridos em transação no banco relacional.

## Desenvolvimento e verificação funcional

O protótipo foi desenvolvido de forma incremental. Primeiro foram implementados o esquema relacional e o importador idempotente. Em seguida foram acrescentadas as consultas de indicadores, a API, o dashboard, os filtros e a fila de oportunidades. A preparação para uso multiempresa incluiu autenticação, associação entre usuários e organizações, papéis de acesso e políticas de segurança em nível de linha no PostgreSQL. O modo SQLite foi mantido para demonstração local reproduzível. A camada de linguagem natural foi posicionada depois das funções analíticas porque suas respostas dependerão desses resultados controlados.

A verificação funcional foi orientada pelos critérios de aceite definidos para cada incremento. Foram exercitados importação válida e inválida, atomicidade, reimportação, totais de referência, filtros, paginação, autenticação, autorização e isolamento organizacional. Os testes automatizados foram complementados por inspeção visual da interface em larguras de celular e desktop. No PostgreSQL remoto, as políticas e funções foram verificadas com identidades sintéticas em transações revertidas. Para o assistente, o protocolo deverá usar perguntas com respostas conhecidas e verificar valor numérico, período, filtros, recusa diante de dados ausentes e fidelidade às funções chamadas.

## Avaliação preditiva

O experimento retrospectivo formulou uma classificação binária no instante de entrada da oportunidade no estágio `Engaging`. O desfecho é o encerramento como `Won` ou `Lost`. Identificador, estágio final, data de fechamento e valor de fechamento foram excluídos das variáveis preditoras por conterem informação posterior ou diretamente relacionada ao resultado.

Os exemplos foram ordenados pela data de engajamento. Registros anteriores a 18 de setembro de 2017 compuseram o conjunto de treinamento, e os registros posteriores formaram o teste final. Todo o pré-processamento foi ajustado apenas no treinamento, procedimento que evita o vazamento de informações entre os conjuntos (SCIKIT-LEARN DEVELOPERS, 2026a). A implementação utiliza pipelines para aplicar codificação às variáveis categóricas, padronizar as variáveis numéricas e treinar regressão logística e árvore de decisão (SCIKIT-LEARN DEVELOPERS, 2026b). A avaliação calculou Average Precision, área sob a curva ROC, Brier score, precisão nos 20% primeiros itens do ranking e lift no mesmo corte. Intervalos bootstrap pareados foram usados para a diferença de Average Precision contra o baseline.

## Aspectos éticos e limites do método

A base utilizada é pública e fictícia, sem dados pessoais de clientes reais. Ela é adequada para demonstrar importação, consultas e avaliação retrospectiva, mas não representa a diversidade de processos comerciais de pequenas e médias empresas. Por isso, os resultados são apresentados como evidência técnica, e não como validação comercial.

Uma etapa futura com dados reais deverá definir a finalidade do tratamento, restringir o acesso e observar os princípios e as bases legais aplicáveis à proteção de dados pessoais (BRASIL, 2018). A avaliação com usuários também deverá informar objetivos, tarefas, métricas e forma de participação. Até que essas etapas ocorram, o sistema não automatiza decisões, contatos ou recomendações comerciais de alto impacto.

## Base de dados

Foi selecionada para a demonstração a base CRM Sales Opportunities, publicada pela Maven Analytics. A página da fonte descreve oportunidades B2B de uma empresa fictícia de hardware e declara origem data.world e licença Public Domain. O download oficial exige autenticação. Por isso, os cinco arquivos foram obtidos de um espelho público, fixado na revisão `9738c487307eb45d270c6ee5d641607bbb8f2a12`. O manifesto local registra URL, tamanho e SHA-256 de cada arquivo. Ainda não foi feita comparação byte a byte com um pacote oficial autenticado.

A auditoria encontrou 8.800 oportunidades, 85 contas, 7 produtos e 35 registros de vendedores. Entre as oportunidades, 4.238 estão marcadas como ganhas, 2.473 como perdidas, 1.589 como em engajamento e 500 como em prospecção. Existem 6.711 negócios encerrados, com taxa observada de ganho de 63,15% nessa população. A soma dos valores dos negócios ganhos é USD 10.005.534. Esse total representa o campo de valor de fechamento e não deve ser interpretado automaticamente como receita contábil.

As ausências seguem o fluxo informado pela própria base. As 500 oportunidades em prospecção não possuem data de engajamento. As 2.089 oportunidades abertas não possuem data nem valor de fechamento. O campo de conta está ausente em 1.425 oportunidades abertas. Esses vazios não foram substituídos por valores fabricados.

A integridade entre contas e vendedores foi confirmada. Foi encontrada uma divergência de produto: 1.480 linhas usam `GTXPro`, enquanto o cadastro contém `GTX Pro`. A preparação aplica um alias explícito e conserva o texto original em uma coluna separada. Os arquivos brutos permanecem inalterados.

## Arquitetura e organização do código

A arquitetura separa a interface web, a API, as regras de negócio, a persistência e o experimento analítico. Essa divisão permite testar cada responsabilidade sem depender da tela e evita que cálculos comerciais sejam refeitos no navegador ou pelo modelo de linguagem. O backend concentra autenticação, importação, consultas de indicadores e regras de priorização. No escopo final, o assistente também deverá acessar o sistema por funções autorizadas, sem executar comandos ou consultas SQL produzidas livremente.

O código Python foi organizado no pacote `src/tcc_sales`. O arquivo `dataset.py` define os cabeçalhos esperados e as funções de conversão; `importer.py` valida e grava os lotes; `metrics.py` contém as consultas analíticas; `auth.py` concentra a comunicação com o serviço de autenticação; e `api.py` reúne as rotas HTTP e escolhe o backend de dados. O experimento preditivo ficou em um script separado, o que impede que uma execução de treinamento seja acionada pelas rotas usadas no dashboard. A interface está nos arquivos `web/index.html`, `web/styles.css` e `web/app.js`.

A aplicação pode operar em dois modos. O SQLite mantém a demonstração local simples e reproduzível. O PostgreSQL do Supabase representa a arquitetura multiempresa, com autenticação e políticas aplicadas no banco. A seleção ocorre por configuração do ambiente, mas as respostas da API mantêm a mesma estrutura. Desse modo, a interface não precisa conhecer detalhes de conexão nem receber credenciais do banco.

O código-fonte, os scripts de reprodução, os testes automatizados e os arquivos que compõem esta entrega estão disponíveis no repositório público do projeto (CASERI, 2026). O repositório não inclui credenciais, banco local nem os CSVs brutos; esses dados podem ser obtidos pelo script de download a partir das URLs e dos hashes registrados no manifesto.

## Importação e persistência dos dados

O fluxo de importação começa em `dataset.py`. A função de leitura compara o cabeçalho recebido com a sequência prevista para cada CSV, remove espaços nas extremidades dos campos e converte datas e números. Em seguida, `validate` confere chaves obrigatórias, duplicidades, referências entre arquivos e combinações válidas de estágio, data de engajamento, data de fechamento e valor. O alias de `GTXPro` para `GTX Pro` é aplicado somente à coluna normalizada; o valor original permanece armazenado em `source_product`.

Somente depois da validação integral o módulo `importer.py` abre a transação de gravação. O identificador do lote é calculado com SHA-256 sobre os nomes e o conteúdo dos quatro arquivos em ordem fixa. Antes de inserir, o importador procura uma execução concluída com o mesmo resumo. Se ela existir, retorna `skipped`; caso contrário, atualiza cadastros, grava oportunidades e registra a execução. As tabelas usam chaves compostas com `tenant_id`, e o SQLite verifica as chaves estrangeiras. O controle transacional utiliza a interface `sqlite3` da biblioteca padrão do Python (PYTHON SOFTWARE FOUNDATION, 2026).

O endpoint de importação recebe obrigatoriamente contas, produtos, equipes e oportunidades. O código aceita apenas extensão CSV, rejeita arquivo vazio ou com indício de conteúdo binário, limita cada item a 10 MB e usa um diretório temporário que é descartado ao final. O banco só é alterado quando o conjunto completo passa pelas verificações. No teste local, a primeira execução gravou 8.800 oportunidades e a repetição do mesmo lote não criou duplicatas.

## API com autenticação e isolamento dos dados

A API foi construída com FastAPI e modelos de entrada tipados. Os parâmetros de período, estágio, produto, gestor, vendedor, limite e deslocamento recebem restrições antes de chegar às consultas. As rotas expõem sessão, cadastro, login, logout, verificação de saúde, resumo comercial, série mensal, desempenho por produto, opções de filtro, oportunidades abertas e importação. Essa organização segue o uso de declarações de parâmetros e validação descrito na documentação do framework (FASTAPI, 2026).

No modo autenticado, `auth.py` envia as credenciais ao Supabase Auth e converte falhas do serviço em mensagens adequadas para a interface. O backend armazena os tokens de acesso e renovação em cookies HttpOnly com `SameSite=Lax`. A aplicação consulta a associação do usuário a uma organização e autoriza importações apenas para os papéis `owner` e `admin`. O identificador da organização usado nas consultas é obtido dessa associação, e não do valor enviado pelo navegador.

Foram aplicadas seis migrations no PostgreSQL 17 do Supabase. Elas criam organizações, associações de usuários, papéis, índices, funções analíticas e a importação transacional. As sete tabelas públicas utilizam segurança em nível de linha. Esse recurso permite definir políticas que restringem as linhas acessíveis ao usuário autenticado (SUPABASE, 2026). As funções remotas são executadas com `security invoker`, preservando as permissões da sessão. A verificação realizada encontrou 24 políticas e duas funções privadas de autorização. Os testes com identidades sintéticas confirmaram leitura da própria organização e bloqueio de inserção cruzada, mas foram revertidos ao final.

## Interface de indicadores e fila de revisão

A interface foi implementada com HTML, CSS e JavaScript, sem uma etapa adicional de compilação. O arquivo `app.js` consulta os endpoints com `fetch`, atualiza os indicadores e mantém o estado dos filtros e da paginação. Valores vindos da API são inseridos como texto ou passam por uma função de escape antes de compor trechos de HTML. A tela também trata autenticação, seleção dos quatro arquivos, mensagens de validação e atualização do painel depois de uma importação.

As consultas de `metrics.py` calculam o total e o valor dos negócios ganhos, a taxa observada de ganho, o ciclo médio, a composição do funil, a evolução mensal e o desempenho por produto. A taxa usa o denominador `Won + Lost`, excluindo oportunidades abertas. Datas de início e fim são aplicadas ao fechamento dos negócios e são devolvidas com a resposta, juntamente com a definição dos indicadores. As consultas usam parâmetros separados dos comandos SQL e sempre incluem a organização correspondente.

A fila de oportunidades abertas foi mantida auditável porque o experimento não sustentou uma probabilidade confiável. O código classifica para revisão imediata oportunidades em `Engaging` abertas há pelo menos noventa dias. Casos com 45 a 89 dias, assim como registros em prospecção sem conta, recebem atenção. Os demais ficam em acompanhamento. A data de referência é a última data de fechamento disponível na própria base. O texto exibido informa a condição aplicada e não apresenta essa regra como probabilidade de venda ou como tempo desde o último contato.

## Experimento preditivo inicial

O experimento formulou uma classificação binária retrospectiva: prever se uma oportunidade encerrada será marcada como `Won` ou `Lost` no instante registrado como entrada em `Engaging`. Foram excluídos o identificador da oportunidade e os campos `deal_stage`, `close_date` e `close_value`. As variáveis utilizadas incluem vendedor, produto, conta, setor, localização, gestor, escritório regional, características da conta, preço do produto, mês e dia da semana do engajamento.

Os dados foram ordenados por data de engajamento. Registros anteriores a 18/09/2017 formaram o treino, com 5.350 exemplos; os 1.361 registros restantes formaram o teste. A taxa de ganho caiu de 63,94% no treino para 60,03% no teste, indicando mudança temporal que uma divisão aleatória poderia ocultar. O pré-processamento categórico e numérico foi ajustado apenas no treino por meio de pipelines.

Foram comparados quatro procedimentos: probabilidade constante igual à prevalência do treino, taxa histórica por produto com suavização, regressão logística e árvore de decisão limitada a profundidade cinco e mínimo de cinquenta exemplos por folha. Não houve busca de hiperparâmetros. A precisão média (Average Precision), a área sob a curva ROC, o erro de Brier e o desempenho nos 20% primeiros itens do ranking foram calculados no teste final.

| Modelo | AP / AUC | P@20% / Lift@20% |
| --- | ---: | ---: |
| Prevalência constante | 0,600 / 0,500 | 0,582 / 0,970 |
| Taxa histórica por produto | 0,590 / 0,480 | 0,579 / 0,964 |
| Regressão logística | 0,597 / 0,499 | 0,623 / 1,037 |
| Árvore de decisão | 0,619 / 0,525 | 0,615 / 1,025 |

Os Brier scores foram 0,241 para a prevalência constante, 0,242 para a taxa por produto, 0,248 para a regressão logística e 0,277 para a árvore. A árvore obteve a maior precisão média, mas a diferença bootstrap pareada em relação ao baseline constante apresentou intervalo de 95% entre -0,003 e 0,044. A regressão logística apresentou intervalo entre -0,029 e 0,024. Como ambos incluem zero e os valores de ROC AUC ficaram próximos de 0,5, o experimento não demonstrou melhora conclusiva. O Brier da árvore também foi pior que o baseline, indicando probabilidades pouco confiáveis.

O resultado mostra que, com os campos e a separação temporal utilizados, a base fictícia sustenta análise descritiva, mas não uma priorização preditiva confiável. Por isso, a interface usa regras transparentes e apresenta o aprendizado de máquina como experimento. Uma nova avaliação poderá usar dados reais autorizados, histórico de atividades e um protocolo definido antes da análise.

## Assistente analítico no escopo final

O assistente em linguagem natural completa o fluxo previsto para o protótipo: o usuário formula uma pergunta, a aplicação identifica uma função analítica permitida, o backend valida os parâmetros e consulta o banco, e o assistente apresenta o resultado estruturado. As funções disponíveis deverão cobrir inicialmente o resumo do período, a evolução mensal, a comparação entre produtos e a listagem de oportunidades. Cada resposta deverá informar o período consultado e, quando necessário, explicar o denominador ou a ausência de dados.

Essa camada não receberá autorização para produzir SQL livre nem para executar comandos do sistema. O conteúdo dos arquivos importados será tratado como dado. Quando uma pergunta exigir informação inexistente, como o último contato do vendedor, o assistente deverá informar a limitação em vez de estimar um valor. Também deverão ser registrados a função escolhida, os parâmetros e o resultado devolvido pelo backend, permitindo comparar a resposta apresentada com a consulta de referência.

No recorte avaliado, as funções analíticas que servirão de base ao assistente já estão implementadas, mas a integração com o modelo de linguagem ainda não está concluída. Consequentemente, este capítulo descreve seu desenho e seus critérios de verificação, sem apresentar respostas, latência ou avaliação de usuários como resultados obtidos.

## Verificação funcional do protótipo

Foram executados 23 testes automatizados. Dois cobrem importação multiempresa, idempotência, mensagens de validação e atomicidade; dois verificam o envio dos quatro CSVs pela API, incluindo reimportação sem duplicação e recusa de lote inválido sem alteração dos totais; seis exercitam página inicial, saúde da API, totais de referência, filtros de período, paginação, explicação da fila, limites de consulta, empresa inexistente e apresentação segura de erros; cinco cobrem exigência de sessão, cookies HttpOnly, autorização por papel e derivação da organização; e oito verificam estruturalmente as migrations do Supabase. A suíte completa foi executada no Windows com Python 3.12 e terminou sem falhas.

A interface e a tela de autenticação foram inspecionadas em larguras de celular e desktop, incluindo foco visível, adaptação dos controles e estados sem conteúdo. As migrations também foram aplicadas e testadas diretamente no PostgreSQL remoto. A carga sintética usada nessa verificação foi revertida, portanto os testes sustentam os cenários exercitados, mas não equivalem a uma implantação permanente em uma empresa.

## Ameaças à validade

A base representa uma única organização fictícia. Não há histórico de contatos, motivos de perda, custos, metas ou informação sobre intervenções do vendedor. O treinamento considera apenas negócios encerrados; oportunidades recentes ainda abertas não podem ser rotuladas como perdas, o que cria viés de seleção. Além disso, identidades de contas e vendedores podem refletir padrões específicos do conjunto e não generalizar para outra empresa.

Os intervalos bootstrap medem variação amostral dentro do teste observado, mas não corrigem mudança de domínio nem provam causalidade. A ausência de busca de hiperparâmetros reduz risco de ajustar repetidamente ao teste, porém torna a comparação preliminar. Novas decisões de modelagem devem usar validação interna e preservar um teste final separado.

## Relação entre a implementação e o protótipo final

A implementação avaliada reúne o registro e a auditoria da base, o esquema relacional local, o importador idempotente, o experimento preditivo, as consultas de indicadores, a API, o dashboard responsivo, o envio controlado dos quatro CSVs, a autenticação e os adaptadores SQLite e Supabase com políticas RLS. Esses componentes cobrem a entrada dos dados, o armazenamento, a análise descritiva e a fila de revisão previstas nos objetivos do projeto.

O protótipo final também inclui o assistente em linguagem natural, o registro das funções utilizadas em cada resposta e uma avaliação com perguntas de referência. Essa parte ainda precisa ser concluída no código antes que o trabalho possa informar resultados sobre correção das respostas ou facilidade de uso. O deploy, a carga permanente para contas reais, o teste ponta a ponta com duas contas e a avaliação com usuários também permanecem pendentes. O texto preserva essas diferenças para que o objetivo final oriente o desenvolvimento sem transformar atividades planejadas em evidência já obtida.

## Contribuições técnicas do protótipo avaliado

O protótipo avaliado oferece evidência de que o caminho entre dados tabulares e uma visualização de apoio pode ser reproduzido no conjunto de demonstração. A importação verifica a estrutura do lote antes de gravar os registros, preserva a origem dos dados e evita que uma reimportação idêntica crie duplicações silenciosas. Esse resultado é relevante porque os indicadores e a fila de oportunidades dependem da consistência dessa etapa anterior.

Também houve uma separação prática entre três formas de apoio à decisão. Os indicadores descritivos são obtidos por consultas controladas; a fila inicial usa regras explícitas; e o experimento de aprendizado de máquina permanece identificado como avaliação, sem ser apresentado como recomendação confiável. Essa distinção reduz o risco de atribuir a um modelo preditivo uma segurança que os resultados ainda não sustentam. A autenticação, o vínculo entre usuário e organização e as políticas de segurança em nível de linha complementam essa preocupação ao limitar o acesso aos dados da empresa correspondente.

Os testes automatizados e as verificações diretas no banco remoto dão suporte à correção dos cenários exercitados, mas não comprovam que o sistema seja adequado a qualquer empresa ou situação. A base é fictícia, os dados foram importados para fins de demonstração e a carga permanente em uma organização real ainda não ocorreu. Portanto, o alcance desta etapa é técnico e experimental: o protótipo funciona nos casos verificados, sem que isso seja convertido em evidência de ganho comercial.

## Interpretação do experimento preditivo

O resultado central da avaliação preditiva não é a escolha de um modelo vencedor, mas a ausência de evidência suficiente para utilizar as probabilidades geradas como base principal de priorização. Embora a árvore de decisão tenha alcançado a maior Average Precision no teste final, o intervalo bootstrap para a diferença em relação ao baseline incluiu zero. Os valores de ROC AUC próximos de 0,5 e o Brier score mais alto desse modelo reforçam que a discriminação e a calibração não foram satisfatórias no recorte analisado.

Esse achado é compatível com a necessidade de distinguir métricas técnicas de resultados comerciais. Wu et al. (2024) observam que pesquisas sobre lead scoring frequentemente dão maior atenção ao desempenho do modelo do que à avaliação de seu efeito no trabalho de vendas. Neste estudo, mesmo uma melhora numérica pequena não seria suficiente para afirmar utilidade comercial, pois não houve observação de vendedores, comparação de tarefas nem acompanhamento de conversões após o uso da ferramenta.

A separação temporal foi mantida justamente para aproximar o cenário de uma aplicação futura, em que padrões observados no passado podem mudar. Yan et al. (2015) destacam a presença de bases pequenas, esparsas e sujeitas a alterações no contexto B2B. A queda na taxa de ganho entre treino e teste e a falta de melhoria conclusiva sugerem que os campos disponíveis na base fictícia não capturam informação bastante para uma predição estável. O resultado não invalida o protótipo, mas delimita o que pode ser afirmado sobre ele nesta etapa.

## Implicações para uso comercial e continuidade

Na interface atual, os critérios de ausência de conta e tempo em `Engaging` funcionam como sinais para revisão humana, e não como previsão de que uma oportunidade será ganha ou perdida. Essa escolha mantém os motivos da ordenação visíveis para o usuário e permite que a pessoa responsável avalie o contexto antes de agir. A preocupação é coerente com a defesa de Rudin (2019) por decisões interpretáveis quando uma explicação precisa ser compreendida por quem será afetado ou responsável pelo processo.

A continuidade do trabalho deve começar pela validação operacional: criar contas de teste, realizar a carga permanente autorizada, repetir o isolamento entre organizações em um fluxo ponta a ponta e registrar as limitações encontradas. Depois disso, uma avaliação com usuários pode comparar clareza dos indicadores, facilidade de localizar casos prioritários e adequação das explicações da fila. Essas medidas são mais apropriadas para discutir utilidade do que inferir impacto apenas a partir da execução do software.

Para completar o escopo final, o assistente deverá responder a partir das funções analíticas testadas, sem executar consultas arbitrárias nem tratar dados importados como instruções. Sua avaliação precisa comparar cada resposta com o resultado de referência e registrar período, filtros e função utilizada. Se novos dados reais e autorizados forem usados em outra avaliação preditiva, será necessário definir o protocolo antecipadamente, preservar uma amostra final separada e documentar as condições de acesso e a finalidade do tratamento. Assim, o desenvolvimento pode avançar sem confundir demonstração técnica com validação no ambiente comercial.

## Referências técnicas consultadas nesta etapa

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais. Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm. Acesso em: 14 set. 2026.

CASERI, Leonardo. *Assistente inteligente para análise de vendas: código-fonte do protótipo*. GitHub, 2026. Disponível em: https://github.com/leocaseri8181/assistente-inteligente-vendas-tcc. Acesso em: 14 set. 2026.

MAVEN ANALYTICS. *CRM Sales Opportunities*. [S. l.]: Maven Analytics, 2026. Disponível em: https://mavenanalytics.io/data-playground/crm-sales-opportunities. Acesso em: 14 set. 2026.

SCIKIT-LEARN DEVELOPERS. Common pitfalls and recommended practices. In: SCIKIT-LEARN DEVELOPERS. *Scikit-learn user guide*. [S. l.], 2026a. Disponível em: https://scikit-learn.org/stable/common_pitfalls.html. Acesso em: 14 set. 2026.

SCIKIT-LEARN DEVELOPERS. LogisticRegression; DecisionTreeClassifier; average_precision_score. In: SCIKIT-LEARN DEVELOPERS. *Scikit-learn API reference*. [S. l.], 2026b. Disponível em: https://scikit-learn.org/stable/. Acesso em: 14 set. 2026.

PYTHON SOFTWARE FOUNDATION. sqlite3 - DB-API 2.0 interface for SQLite databases. In: PYTHON SOFTWARE FOUNDATION. *Python 3.12 documentation*. [S. l.], 2026. Disponível em: https://docs.python.org/3.12/library/sqlite3.html. Acesso em: 14 set. 2026.

FASTAPI. *FastAPI documentation*. [S. l.]: FastAPI, 2026. Disponível em: https://fastapi.tiangolo.com/. Acesso em: 14 set. 2026.

SUPABASE. Row Level Security. In: SUPABASE. *Supabase Docs*. [S. l.], 2026. Disponível em: https://supabase.com/docs/guides/database/postgres/row-level-security. Acesso em: 14 set. 2026.
