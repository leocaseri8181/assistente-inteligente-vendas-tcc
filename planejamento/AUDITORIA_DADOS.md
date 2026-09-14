# Auditoria da base Maven CRM Sales Opportunities

Auditoria executada nos arquivos registrados em `data/manifest.json`. A fonte descreve uma empresa B2B fictícia de hardware. Os arquivos vieram de um espelho público fixado na revisão informada no manifesto; não houve comparação byte a byte com o download oficial autenticado.

## Resultado

- 8.800 oportunidades com identificadores únicos e sem linhas integralmente duplicadas.
- 4.238 ganhas, 2.473 perdidas, 1.589 em engajamento e 500 em prospecção.
- 6.711 negócios encerrados. A taxa observada de ganho entre encerrados é 63.15%.
- Soma do valor de fechamento dos negócios ganhos: USD 10,005,534. O dicionário chama esse campo de receita do negócio; não equivale necessariamente a receita contábil.
- Engajamentos entre 2016-10-20 e 2017-12-27; fechamentos entre 2017-03-01 e 2017-12-31.
- Nenhum fechamento anterior ao engajamento.
- Chaves de conta e vendedor usadas no pipeline existem nas tabelas correspondentes.
- Há 1480 registros com `GTXPro`, enquanto o cadastro contém `GTX Pro`. A preparação aplica esse único alias e preserva o valor original em `source_product`.

## Ausências relevantes

- `account`: 1.425 ausências, concentradas em oportunidades abertas.
- `engage_date`: 500 ausências, correspondentes a `Prospecting`.
- `close_date` e `close_value`: 2.089 ausências, correspondentes às oportunidades abertas.
- `subsidiary_of`: 70 ausências; nesse campo, vazio significa ausência de controladora informada.

Essas ausências são coerentes com os estágios e não devem ser preenchidas com valores inventados.

## Decisão de uso

A base foi aprovada para a demonstração do importador, banco, dashboard e lista de oportunidades. Foi aprovada com ressalvas para um experimento retrospectivo de classificação entre `Won` e `Lost`, no instante de entrada em `Engaging`.

Campos posteriores ao desfecho (`deal_stage`, `close_date` e `close_value`) ficam fora das variáveis preditoras. O experimento não inclui `Prospecting`, pois esse estágio não possui `engage_date`, e não usa as oportunidades abertas como exemplos negativos. O teste temporal reduz, mas não elimina, o risco de viés. Resultados nesta base não validam ganho financeiro nem generalização comercial.

## Limites para o produto

Não calcular tempo sem contato, margem, atingimento de meta ou retorno de marketing. Esses campos não existem. Na versão comercial, o modelo deverá ser treinado e validado separadamente para dados autorizados de cada cliente; sem histórico suficiente, o sistema deve apresentar indicadores e regras transparentes.
