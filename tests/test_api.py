import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcc_sales.api import create_app
from tcc_sales.auth import AuthServiceError, _safe_auth_message
from tcc_sales.importer import connect, import_folder


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        database = Path(cls.temp.name) / "api.sqlite3"
        with closing(connect(database)) as connection:
            import_folder(connection, ROOT / "data/raw/maven")
        cls.client = TestClient(create_app(database))

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp.cleanup()

    def test_dashboard_and_health_are_available(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Onde olhar primeiro", page.text)

    def test_supabase_auth_errors_are_presented_in_portuguese(self):
        self.assertEqual(
            _safe_auth_message(400, {"error_code": "email_address_invalid"}),
            "Informe um endereço de e-mail válido.",
        )
        self.assertEqual(
            _safe_auth_message(400, {"error_code": "email_not_confirmed"}),
            "Confirme o e-mail recebido antes de entrar.",
        )
        self.assertEqual(
            _safe_auth_message(429, {"error_code": "over_email_send_rate_limit"}),
            "O limite de e-mails de confirmação do projeto foi atingido. "
            "Aguarde cerca de uma hora antes de tentar novamente.",
        )
        self.assertEqual(
            _safe_auth_message(429, {"error_code": "over_request_rate_limit"}),
            "Muitas solicitações deste dispositivo. Aguarde alguns minutos e tente novamente.",
        )

    def test_summary_uses_explicit_denominator_and_matches_source(self):
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pipeline_snapshot"], {
            "total": 8800, "prospecting": 500, "engaging": 1589, "won": 4238, "lost": 2473,
        })
        self.assertEqual(data["closed_period"]["closed_count"], 6711)
        self.assertAlmostEqual(data["closed_period"]["win_rate"], 4238 / 6711)
        self.assertEqual(data["closed_period"]["won_value"], 10005534.0)
        self.assertEqual(data["period"], {"date_from": "2017-03-01", "date_to": "2017-12-31", "basis": "close_date"})

    def test_period_filter_and_validation(self):
        filtered = self.client.get("/api/summary", params={"date_from": "2017-12-01", "date_to": "2017-12-31"})
        self.assertEqual(filtered.status_code, 200)
        self.assertLess(filtered.json()["closed_period"]["closed_count"], 6711)
        invalid = self.client.get("/api/summary", params={"date_from": "2017-12-31", "date_to": "2017-01-01"})
        self.assertEqual(invalid.status_code, 422)

    def test_open_opportunities_are_paginated_and_explained(self):
        response = self.client.get("/api/opportunities", params={"limit": 10})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2089)
        self.assertEqual(len(data["items"]), 10)
        self.assertTrue(all(item["stage"] in {"Engaging", "Prospecting"} for item in data["items"]))
        self.assertTrue(all(item["review_reason"] for item in data["items"]))
        self.assertIn("not an ML probability", data["ranking_definition"])

    def test_filters_unknown_tenant_and_limits(self):
        options = self.client.get("/api/options").json()
        product = options["products"][0]
        filtered = self.client.get("/api/opportunities", params={"product": product, "stage": "Engaging", "limit": 5})
        self.assertEqual(filtered.status_code, 200)
        self.assertTrue(all(item["product"] == product and item["stage"] == "Engaging" for item in filtered.json()["items"]))
        self.assertEqual(self.client.get("/api/summary", params={"tenant_id": "missing"}).status_code, 404)
        self.assertEqual(self.client.get("/api/opportunities", params={"limit": 101}).status_code, 422)

    def upload_payload(self, overrides=None):
        overrides = overrides or {}
        files = {}
        for filename, field in {
            "accounts.csv": "accounts",
            "products.csv": "products",
            "sales_teams.csv": "sales_teams",
            "sales_pipeline.csv": "sales_pipeline",
        }.items():
            content = overrides.get(filename, (ROOT / "data/raw/maven" / filename).read_bytes())
            files[field] = (filename, content, "text/csv")
        return files

    def test_csv_upload_is_idempotent(self):
        response = self.client.post("/api/imports", files=self.upload_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "skipped")
        self.assertEqual(response.json()["row_count"], 8800)
        self.assertEqual(len(response.json()["files"]), 4)

    def test_invalid_csv_upload_is_rejected_without_changing_data(self):
        invalid_accounts = b"wrong,header\nvalue,value\n"
        response = self.client.post("/api/imports", files=self.upload_payload({"accounts.csv": invalid_accounts}))
        self.assertEqual(response.status_code, 422)
        self.assertIn("não passaram", response.json()["detail"]["message"])
        self.assertEqual(self.client.get("/api/summary").json()["pipeline_snapshot"]["total"], 8800)


class FakeAuthClient:
    def __init__(self, role="owner"):
        self.role = role
        self.logged_out = False
        self.rpc_calls = []

    def signup(self, email, password, company_name):
        return {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}

    def login(self, email, password):
        if password == "wrong-password":
            raise AuthServiceError(400, "E-mail ou senha inválidos, ou e-mail ainda não confirmado.")
        return {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}

    def refresh(self, refresh_token):
        return {"access_token": "access", "refresh_token": "refresh-2", "expires_in": 3600}

    def user(self, access_token):
        if access_token != "access":
            raise AuthServiceError(401, "Sessão inválida.")
        return {"id": "user-1", "email": "gestor@example.com"}

    def memberships(self, access_token):
        return [{
            "organization_id": 1,
            "role": self.role,
            "organizations": {"id": 1, "name": "Empresa Teste", "slug": "workspace-test"},
        }]

    def logout(self, access_token):
        self.logged_out = True

    def rpc(self, access_token, function_name, parameters):
        self.rpc_calls.append((function_name, parameters))
        if function_name == "sales_analytics":
            return {
                "summary": {"tenant_id": str(parameters["p_organization_id"])},
                "trends": [{"month": "2017-01"}],
                "products": [{"product": "GTX Pro"}],
                "options": {"products": ["GTX Pro"], "managers": [], "agents": [], "stages": ["Engaging", "Prospecting"]},
            }
        if function_name == "import_sales_dataset":
            return {
                "status": "imported",
                "row_count": len(parameters["p_payload"]["opportunities"]),
                "dataset_hash": parameters["p_dataset_hash"],
            }
        return {"total": 0, "limit": parameters["p_limit"], "offset": parameters["p_offset"], "items": []}


class AuthenticatedApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temp.name) / "auth-api.sqlite3"
        with closing(connect(cls.database)) as connection:
            import_folder(connection, ROOT / "data/raw/maven")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.auth = FakeAuthClient()
        self.client = TestClient(create_app(self.database, auth_client=self.auth, auth_required=True))

    def tearDown(self):
        self.client.close()

    def login(self):
        return self.client.post(
            "/api/auth/login",
            json={"email": "gestor@example.com", "password": "senha-segura"},
        )

    def test_protected_routes_require_session(self):
        self.assertEqual(self.client.get("/api/summary").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/session").json(), {
            "auth_enabled": True,
            "authenticated": False,
            "data_backend": "sqlite",
        })

    def test_login_uses_http_only_cookies_and_exposes_safe_session(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        cookies = response.headers.get_list("set-cookie")
        self.assertTrue(any("tcc_access_token=" in value and "HttpOnly" in value for value in cookies))
        self.assertTrue(any("tcc_refresh_token=" in value and "HttpOnly" in value for value in cookies))
        session = self.client.get("/api/auth/session").json()
        self.assertTrue(session["authenticated"])
        self.assertEqual(session["user"]["email"], "gestor@example.com")
        self.assertEqual(session["data_backend"], "sqlite")
        self.assertNotIn("access_token", session)
        self.assertEqual(self.client.get("/api/summary").status_code, 200)

    def test_import_requires_owner_or_admin(self):
        self.auth.role = "analyst"
        self.login()
        response = self.client.post("/api/imports", files=self.upload_payload())
        self.assertEqual(response.status_code, 403)

    def test_supabase_backend_derives_organization_from_membership(self):
        remote = TestClient(create_app(
            self.database,
            auth_client=self.auth,
            auth_required=True,
            data_backend="supabase",
        ))
        try:
            remote.post(
                "/api/auth/login",
                json={"email": "gestor@example.com", "password": "senha-segura"},
            )
            response = remote.get("/api/summary", params={"tenant_id": "empresa-de-outro-usuario"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["tenant_id"], "1")
            self.assertEqual(self.auth.rpc_calls[-1][1]["p_organization_id"], 1)
        finally:
            remote.close()

    def test_supabase_import_is_validated_and_uses_authenticated_organization(self):
        remote = TestClient(create_app(
            self.database,
            auth_client=self.auth,
            auth_required=True,
            data_backend="supabase",
        ))
        try:
            remote.post(
                "/api/auth/login",
                json={"email": "gestor@example.com", "password": "senha-segura"},
            )
            response = remote.post(
                "/api/imports",
                data={"tenant_id": "empresa-de-outro-usuario", "tenant_name": "Ignorada"},
                files=self.upload_payload(),
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["row_count"], 8800)
            function_name, parameters = self.auth.rpc_calls[-1]
            self.assertEqual(function_name, "import_sales_dataset")
            self.assertEqual(parameters["p_organization_id"], 1)
            self.assertEqual(len(parameters["p_payload"]["opportunities"]), 8800)
            self.assertIsInstance(parameters["p_payload"]["opportunities"][0]["engage_date"], (str, type(None)))
        finally:
            remote.close()

    def upload_payload(self):
        return {
            field: (filename, (ROOT / "data/raw/maven" / filename).read_bytes(), "text/csv")
            for filename, field in {
                "accounts.csv": "accounts",
                "products.csv": "products",
                "sales_teams.csv": "sales_teams",
                "sales_pipeline.csv": "sales_pipeline",
            }.items()
        }


if __name__ == "__main__":
    unittest.main()
