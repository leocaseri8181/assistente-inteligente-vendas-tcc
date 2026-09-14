# Migração para PostgreSQL/Supabase

## Estado desta etapa

A estrutura local do Supabase foi inicializada e seis migrations foram aplicadas ao projeto remoto `PROJETO_TCC_VIGENTE`, em São Paulo, com PostgreSQL 17. A verificação remota confirmou sete tabelas com RLS, 24 políticas, duas funções privadas de autorização, o gatilho de provisionamento de empresa e três RPCs autenticadas para indicadores, fila e importação. O advisor de segurança não encontrou problemas após o endurecimento do importador para `security invoker`; os avisos de desempenho restantes são somente índices ainda não utilizados em um banco vazio. Testes remotos transacionais confirmaram isolamento, importação, idempotência e leitura analítica, sem manter usuários ou dados sintéticos. O FastAPI possui adaptadores para SQLite e Supabase, selecionados por configuração.

## Modelo de autorização

- `organizations` representa cada empresa cliente.
- `organization_members` associa usuários do Supabase Auth à empresa com papel `owner`, `admin` ou `analyst`.
- Todas as tabelas comerciais carregam `organization_id` e têm Row Level Security habilitada.
- Membros podem consultar somente organizações às quais pertencem.
- Apenas `owner` e `admin` podem alterar cadastros, oportunidades ou executar importações.
- O papel `anon` não recebe acesso às tabelas comerciais.
- Funções auxiliares de autorização ficam no schema não exposto `private`, usam `search_path` vazio e consultam `auth.uid()`.
- A chave secreta de serviço não é necessária no fluxo implementado e nunca deve ser enviada ao navegador. O backend encaminha o token do usuário, e PostgreSQL e RLS aplicam as permissões da própria sessão.

## Arquivos

- `supabase/config.toml`: configuração local, alinhada ao PostgreSQL 17 do projeto vigente.
- `supabase/migrations/20260908202318_create_sales_workspace.sql`: tabelas, restrições, índices, privilégios e políticas RLS.
- `supabase/migrations/20260908203919_index_organizations_created_by.sql`: índice corretivo indicado pelo advisor de desempenho.
- `supabase/migrations/20260908205050_provision_organization_on_signup.sql`: criação transacional da organização e do primeiro membro `owner` após o cadastro.
- `supabase/migrations/20260908230000_add_authenticated_sales_rpc.sql`: consultas analíticas e fila executadas com a identidade autenticada.
- `supabase/migrations/20260908233000_add_authenticated_sales_import_rpc.sql`: importação atômica e idempotente do conjunto validado.
- `supabase/migrations/20260909021000_harden_import_rpc_invoker.sql`: execução do importador com privilégios do usuário e RLS ativa.
- `.env.example`: nomes das variáveis necessárias, sem credenciais reais.

## Próxima execução

1. Criar a primeira conta real pela interface e confirmar o e-mail, quando exigido pela configuração do Supabase Auth.
2. Importar os quatro CSVs fictícios pela interface já autenticada.
3. Conferir no dashboard remoto os totais de referência e a reimportação idempotente.
4. Repetir o teste de isolamento ponta a ponta com duas contas reais de teste, além dos testes transacionais já executados diretamente no banco.

## Decisões pendentes

- Se analistas terão apenas leitura ou poderão importar arquivos em versões futuras.
- Estratégia de conexão do FastAPI no deploy e provedor de hospedagem.
