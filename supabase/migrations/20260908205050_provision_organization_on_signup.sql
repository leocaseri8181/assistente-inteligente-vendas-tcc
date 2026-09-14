create or replace function private.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  organization_name text;
  new_organization_id bigint;
begin
  organization_name := left(
    coalesce(
      nullif(btrim(new.raw_user_meta_data ->> 'company_name'), ''),
      'Espaço de ' || split_part(coalesce(new.email, 'usuário'), '@', 1)
    ),
    120
  );
  if length(organization_name) < 2 then
    organization_name := 'Nova empresa';
  end if;

  insert into public.organizations (name, slug, created_by)
  values (organization_name, 'workspace-' || replace(new.id::text, '-', ''), new.id)
  returning id into new_organization_id;

  insert into public.organization_members (organization_id, user_id, role)
  values (new_organization_id, new.id, 'owner');

  return new;
end;
$$;

revoke all on function private.handle_new_auth_user() from public, anon, authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function private.handle_new_auth_user();
