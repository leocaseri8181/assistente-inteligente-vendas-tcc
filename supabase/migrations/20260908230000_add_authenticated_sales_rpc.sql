begin;

create or replace function public.sales_analytics(
  p_organization_id bigint,
  p_date_from date default null,
  p_date_to date default null
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  result jsonb;
begin
  if p_date_from is not null and p_date_to is not null and p_date_from > p_date_to then
    raise exception 'date_from must not be after date_to' using errcode = '22007';
  end if;
  if not private.is_organization_member(p_organization_id) then
    raise exception 'organization access denied' using errcode = '42501';
  end if;

  with available as (
    select min(close_date) as first_date, max(close_date) as last_date
    from public.opportunities
    where organization_id = p_organization_id and close_date is not null
  ), stage_counts as (
    select deal_stage, count(*)::integer as quantity
    from public.opportunities
    where organization_id = p_organization_id
    group by deal_stage
  ), closed as (
    select
      count(*) filter (where deal_stage = 'Won')::integer as won_count,
      count(*) filter (where deal_stage = 'Lost')::integer as lost_count,
      coalesce(sum(close_value) filter (where deal_stage = 'Won'), 0)::numeric as won_value,
      avg(close_value) filter (where deal_stage = 'Won')::numeric as average_won_value,
      avg(close_date - engage_date)::numeric as average_cycle_days
    from public.opportunities
    where organization_id = p_organization_id
      and deal_stage in ('Won', 'Lost')
      and (p_date_from is null or close_date >= p_date_from)
      and (p_date_to is null or close_date <= p_date_to)
  ), trends as (
    select coalesce(jsonb_agg(jsonb_build_object(
      'month', month,
      'won_count', won_count,
      'lost_count', lost_count,
      'won_value', won_value
    ) order by month), '[]'::jsonb) as value
    from (
      select to_char(close_date, 'YYYY-MM') as month,
        count(*) filter (where deal_stage = 'Won')::integer as won_count,
        count(*) filter (where deal_stage = 'Lost')::integer as lost_count,
        coalesce(sum(close_value) filter (where deal_stage = 'Won'), 0)::numeric as won_value
      from public.opportunities
      where organization_id = p_organization_id
        and deal_stage in ('Won', 'Lost')
        and (p_date_from is null or close_date >= p_date_from)
        and (p_date_to is null or close_date <= p_date_to)
      group by to_char(close_date, 'YYYY-MM')
    ) rows_by_month
  ), products as (
    select coalesce(jsonb_agg(jsonb_build_object(
      'product', product_name,
      'won_count', won_count,
      'lost_count', lost_count,
      'closed_count', won_count + lost_count,
      'win_rate', case when won_count + lost_count = 0 then null else won_count::numeric / (won_count + lost_count) end,
      'won_value', won_value,
      'sales_price', sales_price
    ) order by won_value desc, product_name), '[]'::jsonb) as value
    from (
      select o.product as product_name,
        count(*) filter (where o.deal_stage = 'Won')::integer as won_count,
        count(*) filter (where o.deal_stage = 'Lost')::integer as lost_count,
        coalesce(sum(o.close_value) filter (where o.deal_stage = 'Won'), 0)::numeric as won_value,
        p.sales_price
      from public.opportunities o
      join public.products p
        on p.organization_id = o.organization_id and p.product_name = o.product
      where o.organization_id = p_organization_id
        and o.deal_stage in ('Won', 'Lost')
        and (p_date_from is null or o.close_date >= p_date_from)
        and (p_date_to is null or o.close_date <= p_date_to)
      group by o.product, p.sales_price
    ) rows_by_product
  ), options as (
    select jsonb_build_object(
      'products', coalesce((select jsonb_agg(product_name order by product_name) from public.products where organization_id = p_organization_id), '[]'::jsonb),
      'managers', coalesce((select jsonb_agg(manager order by manager) from (select distinct manager from public.sales_agents where organization_id = p_organization_id) m), '[]'::jsonb),
      'agents', coalesce((select jsonb_agg(agent_name order by agent_name) from public.sales_agents where organization_id = p_organization_id), '[]'::jsonb),
      'stages', '["Engaging", "Prospecting"]'::jsonb
    ) as value
  )
  select jsonb_build_object(
    'summary', jsonb_build_object(
      'tenant_id', p_organization_id::text,
      'snapshot_date', available.last_date,
      'period', jsonb_build_object(
        'date_from', coalesce(p_date_from, available.first_date),
        'date_to', coalesce(p_date_to, available.last_date),
        'basis', 'close_date'
      ),
      'pipeline_snapshot', jsonb_build_object(
        'total', coalesce((select sum(quantity) from stage_counts), 0),
        'prospecting', coalesce((select quantity from stage_counts where deal_stage = 'Prospecting'), 0),
        'engaging', coalesce((select quantity from stage_counts where deal_stage = 'Engaging'), 0),
        'won', coalesce((select quantity from stage_counts where deal_stage = 'Won'), 0),
        'lost', coalesce((select quantity from stage_counts where deal_stage = 'Lost'), 0)
      ),
      'closed_period', jsonb_build_object(
        'closed_count', closed.won_count + closed.lost_count,
        'won_count', closed.won_count,
        'lost_count', closed.lost_count,
        'win_rate', case when closed.won_count + closed.lost_count = 0 then null else closed.won_count::numeric / (closed.won_count + closed.lost_count) end,
        'won_value', closed.won_value,
        'average_won_value', closed.average_won_value,
        'average_cycle_days', closed.average_cycle_days
      ),
      'definitions', jsonb_build_object(
        'win_rate', 'Won / (Won + Lost); open opportunities are excluded.',
        'won_value', 'Sum of close_value for Won deals; not necessarily accounting revenue.',
        'average_cycle_days', 'Average calendar days from engage_date to close_date among closed deals.',
        'pipeline_snapshot', 'Current recorded stages at the dataset snapshot; historical stage movements are unavailable.'
      )
    ),
    'trends', trends.value,
    'products', products.value,
    'options', options.value
  ) into result
  from available cross join closed cross join trends cross join products cross join options;

  return result;
end;
$$;

create or replace function public.sales_open_opportunities(
  p_organization_id bigint,
  p_stage text default null,
  p_product text default null,
  p_manager text default null,
  p_agent text default null,
  p_limit integer default 20,
  p_offset integer default 0
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  result jsonb;
begin
  if not private.is_organization_member(p_organization_id) then
    raise exception 'organization access denied' using errcode = '42501';
  end if;
  if p_stage is not null and p_stage not in ('Engaging', 'Prospecting') then
    raise exception 'invalid open stage' using errcode = '22023';
  end if;
  if p_limit < 1 or p_limit > 100 or p_offset < 0 then
    raise exception 'invalid pagination' using errcode = '22023';
  end if;

  with snapshot as (
    select max(close_date) as snapshot_date
    from public.opportunities
    where organization_id = p_organization_id and close_date is not null
  ), filtered as (
    select o.*, a.manager, a.regional_office, snapshot.snapshot_date,
      case when o.engage_date is null then null else snapshot.snapshot_date - o.engage_date end as days_open,
      case
        when o.deal_stage = 'Engaging' and snapshot.snapshot_date - o.engage_date >= 90 then 3
        when o.deal_stage = 'Engaging' and snapshot.snapshot_date - o.engage_date >= 45 then 2
        when o.deal_stage = 'Prospecting' and o.account is null then 2
        else 1
      end as priority_order
    from public.opportunities o
    join public.sales_agents a
      on a.organization_id = o.organization_id and a.agent_name = o.sales_agent
    cross join snapshot
    where o.organization_id = p_organization_id
      and o.deal_stage in ('Engaging', 'Prospecting')
      and (p_stage is null or o.deal_stage = p_stage)
      and (p_product is null or o.product = p_product)
      and (p_manager is null or a.manager = p_manager)
      and (p_agent is null or o.sales_agent = p_agent)
  ), selected as (
    select * from filtered
    order by priority_order desc, days_open desc nulls last, opportunity_key
    limit p_limit offset p_offset
  )
  select jsonb_build_object(
    'snapshot_date', (select snapshot_date from snapshot),
    'total', (select count(*) from filtered),
    'limit', p_limit,
    'offset', p_offset,
    'items', coalesce((select jsonb_agg(jsonb_build_object(
      'opportunity_id', opportunity_key,
      'stage', deal_stage,
      'account', account,
      'product', product,
      'sales_agent', sales_agent,
      'manager', manager,
      'regional_office', regional_office,
      'engage_date', engage_date,
      'days_since_engagement', days_open,
      'review_level', case priority_order when 3 then 'review_now' when 2 then 'attention' else 'routine' end,
      'review_reason', case
        when deal_stage = 'Prospecting' and account is null then 'Prospecção sem conta informada'
        when deal_stage = 'Prospecting' then 'Aguardando início de engajamento'
        else format('Em engajamento há %s dias desde %s', days_open, engage_date)
      end
    ) order by priority_order desc, days_open desc nulls last, opportunity_key) from selected), '[]'::jsonb),
    'ranking_definition', 'Transparent review rule based on recorded stage, missing account, and days since engagement; it is not an ML probability or time since last contact.'
  ) into result;
  return result;
end;
$$;

revoke all on function public.sales_analytics(bigint, date, date) from public, anon;
revoke all on function public.sales_open_opportunities(bigint, text, text, text, text, integer, integer) from public, anon;
grant execute on function public.sales_analytics(bigint, date, date) to authenticated;
grant execute on function public.sales_open_opportunities(bigint, text, text, text, text, integer, integer) to authenticated;

commit;
