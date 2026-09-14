begin;

-- Funções auxiliares de autorização ficam fora do schema exposto pela Data API.
create schema if not exists private;
revoke all on schema private from public;
grant usage on schema private to authenticated;

create table public.organizations (
  id bigint generated always as identity primary key,
  name text not null check (length(btrim(name)) between 2 and 120),
  slug text not null unique check (slug = lower(slug) and slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table public.organization_members (
  organization_id bigint not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'analyst')),
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create index organization_members_user_id_idx
  on public.organization_members (user_id, organization_id);

create table public.accounts (
  id bigint generated always as identity primary key,
  organization_id bigint not null references public.organizations(id) on delete cascade,
  account_name text not null,
  sector text not null,
  year_established integer not null check (year_established between 1800 and 2200),
  revenue_musd numeric(14, 4) not null check (revenue_musd >= 0),
  employees integer not null check (employees >= 0),
  office_location text not null,
  subsidiary_of text,
  created_at timestamptz not null default now(),
  unique (organization_id, account_name)
);

create table public.products (
  id bigint generated always as identity primary key,
  organization_id bigint not null references public.organizations(id) on delete cascade,
  product_name text not null,
  series text not null,
  sales_price numeric(14, 2) not null check (sales_price >= 0),
  created_at timestamptz not null default now(),
  unique (organization_id, product_name)
);

create table public.sales_agents (
  id bigint generated always as identity primary key,
  organization_id bigint not null references public.organizations(id) on delete cascade,
  agent_name text not null,
  manager text not null,
  regional_office text not null,
  created_at timestamptz not null default now(),
  unique (organization_id, agent_name)
);

create table public.opportunities (
  id bigint generated always as identity primary key,
  organization_id bigint not null references public.organizations(id) on delete cascade,
  opportunity_key text not null,
  sales_agent text not null,
  product text not null,
  source_product text not null,
  account text,
  deal_stage text not null check (deal_stage in ('Prospecting', 'Engaging', 'Won', 'Lost')),
  engage_date date,
  close_date date,
  close_value numeric(14, 2),
  created_at timestamptz not null default now(),
  unique (organization_id, opportunity_key),
  foreign key (organization_id, sales_agent)
    references public.sales_agents (organization_id, agent_name),
  foreign key (organization_id, product)
    references public.products (organization_id, product_name),
  foreign key (organization_id, account)
    references public.accounts (organization_id, account_name),
  check (close_date is null or engage_date is null or close_date >= engage_date),
  check (
    (deal_stage = 'Prospecting' and engage_date is null and close_date is null and close_value is null)
    or (deal_stage = 'Engaging' and engage_date is not null and close_date is null and close_value is null)
    or (deal_stage in ('Won', 'Lost') and engage_date is not null and close_date is not null and close_value is not null)
  )
);

create index opportunities_organization_stage_idx
  on public.opportunities (organization_id, deal_stage);
create index opportunities_organization_engage_date_idx
  on public.opportunities (organization_id, engage_date);
create index opportunities_agent_fk_idx
  on public.opportunities (organization_id, sales_agent);
create index opportunities_product_fk_idx
  on public.opportunities (organization_id, product);
create index opportunities_account_fk_idx
  on public.opportunities (organization_id, account);

create table public.import_runs (
  id bigint generated always as identity primary key,
  organization_id bigint not null references public.organizations(id) on delete cascade,
  dataset_hash text not null check (dataset_hash ~ '^[0-9a-f]{64}$'),
  row_count integer not null check (row_count >= 0),
  status text not null check (status in ('succeeded', 'failed')),
  imported_by uuid not null references auth.users(id) on delete restrict,
  imported_at timestamptz not null default now(),
  unique (organization_id, dataset_hash, status)
);

create index import_runs_imported_by_idx on public.import_runs (imported_by);

create or replace function private.is_organization_member(target_organization_id bigint)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.organization_members as membership
    where membership.organization_id = target_organization_id
      and membership.user_id = (select auth.uid())
  );
$$;

create or replace function private.has_organization_role(
  target_organization_id bigint,
  allowed_roles text[]
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.organization_members as membership
    where membership.organization_id = target_organization_id
      and membership.user_id = (select auth.uid())
      and membership.role = any (allowed_roles)
  );
$$;

revoke all on function private.is_organization_member(bigint) from public, anon;
revoke all on function private.has_organization_role(bigint, text[]) from public, anon;
grant execute on function private.is_organization_member(bigint) to authenticated;
grant execute on function private.has_organization_role(bigint, text[]) to authenticated;

alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.accounts enable row level security;
alter table public.products enable row level security;
alter table public.sales_agents enable row level security;
alter table public.opportunities enable row level security;
alter table public.import_runs enable row level security;

create policy organizations_select_member
on public.organizations for select to authenticated
using ((select private.is_organization_member(id)));

create policy organizations_update_admin
on public.organizations for update to authenticated
using ((select private.has_organization_role(id, array['owner', 'admin'])))
with check ((select private.has_organization_role(id, array['owner', 'admin'])));

create policy organization_members_select_member
on public.organization_members for select to authenticated
using ((select private.is_organization_member(organization_id)));

create policy organization_members_insert_admin
on public.organization_members for insert to authenticated
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy organization_members_update_admin
on public.organization_members for update to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])))
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy organization_members_delete_admin
on public.organization_members for delete to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy accounts_select_member
on public.accounts for select to authenticated
using ((select private.is_organization_member(organization_id)));
create policy accounts_insert_admin
on public.accounts for insert to authenticated
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy accounts_update_admin
on public.accounts for update to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])))
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy accounts_delete_admin
on public.accounts for delete to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy products_select_member
on public.products for select to authenticated
using ((select private.is_organization_member(organization_id)));
create policy products_insert_admin
on public.products for insert to authenticated
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy products_update_admin
on public.products for update to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])))
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy products_delete_admin
on public.products for delete to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy sales_agents_select_member
on public.sales_agents for select to authenticated
using ((select private.is_organization_member(organization_id)));
create policy sales_agents_insert_admin
on public.sales_agents for insert to authenticated
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy sales_agents_update_admin
on public.sales_agents for update to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])))
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy sales_agents_delete_admin
on public.sales_agents for delete to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy opportunities_select_member
on public.opportunities for select to authenticated
using ((select private.is_organization_member(organization_id)));
create policy opportunities_insert_admin
on public.opportunities for insert to authenticated
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy opportunities_update_admin
on public.opportunities for update to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])))
with check ((select private.has_organization_role(organization_id, array['owner', 'admin'])));
create policy opportunities_delete_admin
on public.opportunities for delete to authenticated
using ((select private.has_organization_role(organization_id, array['owner', 'admin'])));

create policy import_runs_select_member
on public.import_runs for select to authenticated
using ((select private.is_organization_member(organization_id)));
create policy import_runs_insert_admin
on public.import_runs for insert to authenticated
with check (
  imported_by = (select auth.uid())
  and (select private.has_organization_role(organization_id, array['owner', 'admin']))
);

-- Grants explícitos mantêm a Data API previsível mesmo com autoexposição desativada.
revoke all on public.organizations, public.organization_members, public.accounts,
  public.products, public.sales_agents, public.opportunities, public.import_runs from anon;

grant select, update on public.organizations to authenticated;
grant select, insert, update, delete on public.organization_members to authenticated;
grant select, insert, update, delete on public.accounts, public.products,
  public.sales_agents, public.opportunities to authenticated;
grant select, insert on public.import_runs to authenticated;
grant usage, select on all sequences in schema public to authenticated;

comment on table public.organizations is 'Empresas isoladas por políticas de segurança em nível de linha.';
comment on table public.import_runs is 'Registro imutável dos lotes de CSV importados.';
comment on column public.opportunities.source_product is 'Nome original do produto antes da normalização controlada.';

commit;
