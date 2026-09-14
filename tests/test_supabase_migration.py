import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260908202318_create_sales_workspace.sql"
CONFIG = ROOT / "supabase/config.toml"
MIGRATIONS = ROOT / "supabase/migrations"
PUBLIC_TABLES = {
    "organizations",
    "organization_members",
    "accounts",
    "products",
    "sales_agents",
    "opportunities",
    "import_runs",
}


class SupabaseMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_every_public_table_has_rls_and_authenticated_policy(self):
        created = set(re.findall(r"create table public\.([a-z_]+)", self.sql))
        self.assertEqual(created, PUBLIC_TABLES)
        for table in PUBLIC_TABLES:
            self.assertIn(f"alter table public.{table} enable row level security", self.sql)
            self.assertRegex(
                self.sql,
                rf"create policy [a-z_]+\s+on public\.{table} .*? to authenticated",
            )

    def test_update_policies_check_old_and_new_organization(self):
        update_policies = re.findall(
            r"create policy [a-z_]+\s+on public\.[a-z_]+ for update to authenticated\s+(.*?);",
            self.sql,
            flags=re.DOTALL,
        )
        self.assertGreaterEqual(len(update_policies), 6)
        for policy in update_policies:
            self.assertIn("using", policy)
            self.assertIn("with check", policy)

    def test_authorization_helpers_are_hardened_and_anon_is_revoked(self):
        self.assertIn("create schema if not exists private", self.sql)
        self.assertGreaterEqual(self.sql.count("security definer"), 2)
        self.assertGreaterEqual(self.sql.count("set search_path = ''"), 2)
        self.assertIn("from public, anon", self.sql)
        self.assertNotIn("service_role", self.sql)

    def test_local_auth_and_data_api_defaults_are_safe(self):
        config = CONFIG.read_text(encoding="utf-8")
        self.assertIn('auto_expose_new_tables = false', config)
        self.assertIn('site_url = "http://127.0.0.1:8000"', config)
        self.assertIn('minimum_password_length = 8', config)

    def test_foreign_key_advisor_fix_is_versioned(self):
        all_sql = "\n".join(
            migration.read_text(encoding="utf-8").lower()
            for migration in sorted(MIGRATIONS.glob("*.sql"))
        )
        self.assertIn(
            "create index organizations_created_by_idx\n  on public.organizations (created_by)",
            all_sql,
        )

    def test_signup_provisioning_assigns_owner_server_side(self):
        all_sql = "\n".join(
            migration.read_text(encoding="utf-8").lower()
            for migration in sorted(MIGRATIONS.glob("*.sql"))
        )
        self.assertIn("create or replace function private.handle_new_auth_user()", all_sql)
        self.assertIn("after insert on auth.users", all_sql)
        self.assertIn("values (new_organization_id, new.id, 'owner')", all_sql)
        self.assertNotIn("raw_user_meta_data ->> 'role'", all_sql)

    def test_sales_rpc_uses_invoker_permissions_and_server_membership(self):
        rpc_sql = (MIGRATIONS / "20260908230000_add_authenticated_sales_rpc.sql").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn("create or replace function public.sales_analytics", rpc_sql)
        self.assertIn("create or replace function public.sales_open_opportunities", rpc_sql)
        self.assertGreaterEqual(rpc_sql.count("security invoker"), 2)
        self.assertGreaterEqual(rpc_sql.count("private.is_organization_member(p_organization_id)"), 2)
        self.assertGreaterEqual(rpc_sql.count("from public, anon"), 2)
        self.assertNotIn("security definer", rpc_sql)

    def test_import_rpc_checks_server_role_and_limits_payload(self):
        import_sql = (MIGRATIONS / "20260908233000_add_authenticated_sales_import_rpc.sql").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn("create or replace function public.import_sales_dataset", import_sql)
        self.assertIn("private.has_organization_role(p_organization_id, array['owner', 'admin'])", import_sql)
        self.assertIn("opportunity_count > 20000", import_sql)
        self.assertIn("set search_path = ''", import_sql)
        self.assertIn("from public, anon", import_sql)
        hardening_sql = (MIGRATIONS / "20260909021000_harden_import_rpc_invoker.sql").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn(
            "alter function public.import_sales_dataset(bigint, text, jsonb) security invoker",
            hardening_sql,
        )
        self.assertEqual(hardening_sql.count("grant usage on sequence"), 5)


if __name__ == "__main__":
    unittest.main()
