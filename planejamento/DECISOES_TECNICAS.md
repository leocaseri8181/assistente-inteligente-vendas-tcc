# Decisões técnicas iniciais

## Dados de demonstração

Usar Maven CRM Sales Opportunities na demonstração parcial. Motivo: estrutura B2B com contas, produtos, vendedores e oportunidades, compatível com o fluxo proposto. Condição: sempre identificar os dados como fictícios e registrar a proveniência do espelho público.

## Instante da previsão

Definir o instante experimental como a data de entrada em `Engaging`. Somente informações disponíveis nesse instante podem compor as variáveis preditoras. `deal_stage`, `close_date` e `close_value` ficam excluídos. Registros `Prospecting` não entram porque não possuem `engage_date`; registros abertos não recebem rótulo negativo.

## Uso do resultado de ML

Não integrar o modelo inicial como uma probabilidade comercial validada. No teste temporal, regressão logística e árvore não apresentaram melhora conclusiva sobre o baseline. A primeira interface poderá ordenar oportunidades por regras transparentes, mantendo o experimento de ML como contribuição acadêmica e ponto de evolução com dados reais autorizados.

## Banco de dados

Usar SQLite no protótipo local para reduzir dependências e permitir demonstração reproduzível. O esquema já inclui `tenant_id` em todas as entidades comerciais, preparando a migração para PostgreSQL/Supabase. A autenticação já protege a API quando configurada, mas o SQLite local contém uma única base demonstrativa compartilhada e não demonstra isolamento multiempresa de produção.

A migration inicial do Supabase substitui o identificador textual informado pelo cliente por `organization_id` associado a usuários autenticados em `organization_members`. Todas as sete tabelas públicas têm RLS. Analistas possuem leitura; `owner` e `admin` podem alterar dados. As funções auxiliares de autorização ficam fora do schema exposto e a Data API recebe privilégios explícitos. Uma migration posterior cria, no servidor, a organização e o primeiro `owner` de cada novo cadastro sem aceitar papel vindo dos metadados do usuário. RPCs de leitura e importação recebem a organização derivada da associação autenticada no FastAPI e executam com `security invoker`, mantendo RLS ativa. A implementação foi testada remotamente em transações revertidas; falta a validação ponta a ponta com contas reais.

## Importação

Manter os CSVs brutos imutáveis e fora do versionamento. Validar cabeçalhos, tipos, datas, chaves, referências e coerência entre estágio e datas antes da transação. A reimportação do mesmo conjunto é ignorada pelo hash. O alias `GTXPro` para `GTX Pro` é explícito, e o valor original permanece em `source_product`.

## API e interface local

Usar FastAPI no backend do protótipo e HTML, CSS e JavaScript sem etapa de build na primeira interface. Essa combinação reduz dependências na entrega parcial e mantém cada indicador ligado a uma consulta testável. O backend troca credenciais com o Supabase Auth, valida a identidade no serviço e mantém os tokens em cookies HttpOnly com `SameSite=Lax`; o navegador recebe apenas dados seguros da sessão. Importações exigem papel `owner` ou `admin`. O backend permite escolher `sqlite` ou `supabase`. No modo Supabase, ignora qualquer `tenant_id` enviado pelo navegador e usa o `organization_id` obtido da associação autenticada. O modo SQLite permanece apenas para demonstração local reproduzível e não deve ser confundido com isolamento multiempresa.

Apresentar a priorização como uma fila de revisão explicada. Ausência de conta e idade desde o engajamento são sinais operacionais, não estimativas de conversão nem evidência do efeito de um novo contato. A data de referência deve ser derivada do conjunto ou informada pela empresa para evitar classificar dados históricos como se fossem atuais.

## Assistente com LLM

Adiar a integração até existirem consultas analíticas controladas e testadas. O modelo de linguagem deverá chamar funções que calculam métricas no backend, em vez de calcular livremente a partir do texto. Essa decisão reduz respostas numéricas sem fundamento e mantém período, filtros e denominadores verificáveis.
