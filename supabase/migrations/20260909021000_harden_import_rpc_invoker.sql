begin;

alter function public.import_sales_dataset(bigint, text, jsonb) security invoker;

grant usage on sequence public.accounts_id_seq to authenticated;
grant usage on sequence public.products_id_seq to authenticated;
grant usage on sequence public.sales_agents_id_seq to authenticated;
grant usage on sequence public.opportunities_id_seq to authenticated;
grant usage on sequence public.import_runs_id_seq to authenticated;

commit;
