begin;

create or replace function public.import_sales_dataset(
  p_organization_id bigint,
  p_dataset_hash text,
  p_payload jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller_id uuid := auth.uid();
  opportunity_count integer;
begin
  if caller_id is null
    or not private.has_organization_role(p_organization_id, array['owner', 'admin']) then
    raise exception 'organization import access denied' using errcode = '42501';
  end if;
  if p_dataset_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid dataset hash' using errcode = '22023';
  end if;
  if jsonb_typeof(p_payload) <> 'object'
    or jsonb_typeof(p_payload -> 'accounts') <> 'array'
    or jsonb_typeof(p_payload -> 'products') <> 'array'
    or jsonb_typeof(p_payload -> 'agents') <> 'array'
    or jsonb_typeof(p_payload -> 'opportunities') <> 'array' then
    raise exception 'invalid dataset payload' using errcode = '22023';
  end if;

  opportunity_count := jsonb_array_length(p_payload -> 'opportunities');
  if jsonb_array_length(p_payload -> 'accounts') > 5000
    or jsonb_array_length(p_payload -> 'products') > 5000
    or jsonb_array_length(p_payload -> 'agents') > 5000
    or opportunity_count > 20000 then
    raise exception 'dataset row limit exceeded' using errcode = '54000';
  end if;

  if exists (
    select 1 from public.import_runs
    where organization_id = p_organization_id
      and dataset_hash = p_dataset_hash
      and status = 'succeeded'
  ) then
    return jsonb_build_object(
      'status', 'skipped',
      'reason', 'dataset already imported',
      'row_count', opportunity_count,
      'dataset_hash', p_dataset_hash
    );
  end if;

  insert into public.accounts (
    organization_id, account_name, sector, year_established,
    revenue_musd, employees, office_location, subsidiary_of
  )
  select p_organization_id, row.account, row.sector, row.year_established,
    row.revenue, row.employees, row.office_location, nullif(row.subsidiary_of, '')
  from jsonb_to_recordset(p_payload -> 'accounts') as row(
    account text, sector text, year_established integer, revenue numeric,
    employees integer, office_location text, subsidiary_of text
  )
  on conflict (organization_id, account_name) do update set
    sector = excluded.sector,
    year_established = excluded.year_established,
    revenue_musd = excluded.revenue_musd,
    employees = excluded.employees,
    office_location = excluded.office_location,
    subsidiary_of = excluded.subsidiary_of;

  insert into public.products (organization_id, product_name, series, sales_price)
  select p_organization_id, row.product, row.series, row.sales_price
  from jsonb_to_recordset(p_payload -> 'products') as row(
    product text, series text, sales_price numeric
  )
  on conflict (organization_id, product_name) do update set
    series = excluded.series,
    sales_price = excluded.sales_price;

  insert into public.sales_agents (organization_id, agent_name, manager, regional_office)
  select p_organization_id, row.sales_agent, row.manager, row.regional_office
  from jsonb_to_recordset(p_payload -> 'agents') as row(
    sales_agent text, manager text, regional_office text
  )
  on conflict (organization_id, agent_name) do update set
    manager = excluded.manager,
    regional_office = excluded.regional_office;

  insert into public.opportunities (
    organization_id, opportunity_key, sales_agent, product, source_product,
    account, deal_stage, engage_date, close_date, close_value
  )
  select p_organization_id, row.opportunity_id, row.sales_agent, row.product,
    row.source_product, nullif(row.account, ''), row.deal_stage,
    row.engage_date, row.close_date, row.close_value
  from jsonb_to_recordset(p_payload -> 'opportunities') as row(
    opportunity_id text, sales_agent text, product text, source_product text,
    account text, deal_stage text, engage_date date, close_date date, close_value numeric
  )
  on conflict (organization_id, opportunity_key) do update set
    sales_agent = excluded.sales_agent,
    product = excluded.product,
    source_product = excluded.source_product,
    account = excluded.account,
    deal_stage = excluded.deal_stage,
    engage_date = excluded.engage_date,
    close_date = excluded.close_date,
    close_value = excluded.close_value;

  insert into public.import_runs (
    organization_id, dataset_hash, row_count, status, imported_by
  ) values (
    p_organization_id, p_dataset_hash, opportunity_count, 'succeeded', caller_id
  );

  return jsonb_build_object(
    'status', 'imported',
    'row_count', opportunity_count,
    'dataset_hash', p_dataset_hash
  );
end;
$$;

revoke all on function public.import_sales_dataset(bigint, text, jsonb) from public, anon;
grant execute on function public.import_sales_dataset(bigint, text, jsonb) to authenticated;

commit;
